from __future__ import annotations

import requests
import xml.etree.ElementTree as ET

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

async def search_pubmed(query: str, max_results: int = 10) -> list[dict]:
    # Step 1: get PMIDs
    search_resp = requests.get(ESEARCH_URL, params={
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }, timeout=10)
    search_resp.raise_for_status()
    search_data = search_resp.json()
    pmids = search_data.get("esearchresult", {}).get("idlist", [])

    if not pmids:
        return []

    # Step 2: get paper details
    summary_resp = requests.get(ESUMMARY_URL, params={
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }, timeout=10)
    summary_resp.raise_for_status()
    summary_data = summary_resp.json()
    uids = summary_data.get("result", {}).get("uids", [])

    # Step 3: get abstracts
    fetch_resp = requests.get(EFETCH_URL, params={
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }, timeout=10)
    fetch_resp.raise_for_status()
    abstracts = _parse_abstracts(fetch_resp.text)

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

    return results


def _parse_abstracts(xml_text: str) -> dict[str, str]:
    root = ET.fromstring(xml_text)
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
