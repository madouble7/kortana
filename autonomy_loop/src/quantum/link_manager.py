class LinkManager:
    def __init__(self):
        self.active_links = set()

    def verify_link(self, link_id: str) -> bool:
        return link_id in self.active_links

    def add_link(self, link_id: str):
        self.active_links.add(link_id)