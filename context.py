def extract_keywords(product: str):
    product = product.lower()
    keywords = []

    if "cloud" in product or "cost" in product or "spend" in product or "billing" in product:
        keywords += ["aws", "gcp", "azure", "google cloud platform", "google cloud"]

    if "ai" in product or "ml" in product or "machine learning" in product:
        keywords += ["ai", "ml", "machine learning", "pytorch", "tensorflow"]

    if "security" in product or "compliance" in product:
        keywords += ["security", "compliance", "soc2", "iso27001"]

    if "dev" in product or "devops" in product or "platform" in product or "infra" in product:
        keywords += ["kubernetes", "docker", "terraform", "ansible", "jenkins", "helm"]

    if "data" in product or "pipeline" in product or "analytics" in product:
        keywords += ["data", "analytics", "pipeline", "spark", "kafka", "databricks"]

    if "engineering" in product or "team" in product or "platform" in product:
        keywords += ["aws", "kubernetes", "azure", "gcp", "docker", "terraform"]

    return list(set(keywords))
