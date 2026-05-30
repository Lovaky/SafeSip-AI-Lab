from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET

import requests

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

logger = logging.getLogger(__name__)


class PubMedServiceError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 502,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail


async def search_pubmed(
    query: str,
    max_results: int = 10,
    request_id: str | None = None,
) -> list[dict]:
    logger.info(
        "pubmed.search.start request_id=%s query=%r max_results=%s",
        request_id,
        query,
        max_results,
    )

    search_data = _get_json(
        "esearch",
        ESEARCH_URL,
        {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
        },
        request_id=request_id,
    )
    pmids = search_data.get("esearchresult", {}).get("idlist", [])

    if not pmids:
        logger.info("pubmed.search.empty request_id=%s query=%r", request_id, query)
        return []

    summary_data = _get_json(
        "esummary",
        ESUMMARY_URL,
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        },
        request_id=request_id,
    )
    uids = summary_data.get("result", {}).get("uids", [])

    fetch_text = _get_text(
        "efetch",
        EFETCH_URL,
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        },
        request_id=request_id,
    )
    abstracts = _parse_abstracts(fetch_text, request_id=request_id)

    results = []
    for uid in uids:
        paper = summary_data["result"][uid]
        results.append({
            "title": paper.get("title", ""),
            "abstract": abstracts.get(uid, ""),
            "pubdate": paper.get("pubdate", ""),
            "pmid": uid,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
        })

    logger.info(
        "pubmed.search.success request_id=%s query=%r result_count=%s",
        request_id,
        query,
        len(results),
    )
    return results


async def check_pubmed_health(request_id: str | None = None) -> dict:
    data = _get_json(
        "health_esearch",
        ESEARCH_URL,
        {
            "db": "pubmed",
            "term": "coffee",
            "retmax": 1,
            "retmode": "json",
        },
        request_id=request_id,
        timeout=5,
    )
    ids = data.get("esearchresult", {}).get("idlist", [])
    return {"ok": True, "sample_result_count": len(ids)}


def _get_json(
    endpoint: str,
    url: str,
    params: dict,
    *,
    request_id: str | None,
    timeout: int = 10,
) -> dict:
    response = _request(endpoint, url, params, request_id=request_id, timeout=timeout)
    try:
        return response.json()
    except ValueError as exc:
        logger.exception(
            "pubmed.%s.json_parse_failed request_id=%s",
            endpoint,
            request_id,
        )
        raise PubMedServiceError(
            "pubmed_invalid_json",
            "PubMed returned invalid JSON.",
            detail=str(exc),
        ) from exc


def _get_text(
    endpoint: str,
    url: str,
    params: dict,
    *,
    request_id: str | None,
    timeout: int = 10,
) -> str:
    return _request(endpoint, url, params, request_id=request_id, timeout=timeout).text


def _request(
    endpoint: str,
    url: str,
    params: dict,
    *,
    request_id: str | None,
    timeout: int,
) -> requests.Response:
    started_at = time.perf_counter()
    safe_params = {key: value for key, value in params.items() if key != "api_key"}
    logger.info(
        "pubmed.%s.request request_id=%s params=%s",
        endpoint,
        request_id,
        safe_params,
    )

    try:
        response = requests.get(url, params=params, timeout=timeout)
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "pubmed.%s.response request_id=%s status_code=%s elapsed_ms=%s",
            endpoint,
            request_id,
            response.status_code,
            elapsed_ms,
        )
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout as exc:
        logger.warning(
            "pubmed.%s.timeout request_id=%s timeout=%s",
            endpoint,
            request_id,
            timeout,
            exc_info=True,
        )
        raise PubMedServiceError(
            "pubmed_timeout",
            "PubMed request timed out.",
            detail=str(exc),
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        logger.warning(
            "pubmed.%s.connection_failed request_id=%s",
            endpoint,
            request_id,
            exc_info=True,
        )
        raise PubMedServiceError(
            "pubmed_connection_failed",
            "Unable to connect to PubMed API.",
            detail=str(exc),
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        logger.warning(
            "pubmed.%s.http_error request_id=%s status_code=%s",
            endpoint,
            request_id,
            status_code,
            exc_info=True,
        )
        raise PubMedServiceError(
            "pubmed_http_error",
            f"PubMed API returned HTTP {status_code}.",
            status_code=502,
            detail=str(exc),
        ) from exc
    except requests.exceptions.RequestException as exc:
        logger.warning(
            "pubmed.%s.request_failed request_id=%s",
            endpoint,
            request_id,
            exc_info=True,
        )
        raise PubMedServiceError(
            "pubmed_request_failed",
            "PubMed request failed.",
            detail=str(exc),
        ) from exc


def _parse_abstracts(xml_text: str, request_id: str | None = None) -> dict[str, str]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.exception("pubmed.efetch.xml_parse_failed request_id=%s", request_id)
        raise PubMedServiceError(
            "pubmed_invalid_xml",
            "PubMed returned invalid XML.",
            detail=str(exc),
        ) from exc

    abstracts = {}

    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find(".//MedlineCitation/PMID")
        if pmid_el is None or not pmid_el.text:
            continue

        parts = []
        for abstract_el in article.findall(".//Abstract/AbstractText"):
            text = " ".join(part.strip() for part in abstract_el.itertext() if part.strip())
            if not text:
                continue

            label = abstract_el.attrib.get("Label")
            if label:
                parts.append(f"{label}: {text}")
            else:
                parts.append(text)

        abstracts[pmid_el.text] = "\n".join(parts)

    return abstracts
