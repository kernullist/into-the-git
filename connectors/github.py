import os
from .base import BaseConnector


class GitHubConnector(BaseConnector):
    def __init__(self, repo_url, local_path, branch=None, token=None):
        super().__init__(repo_url, local_path, branch)
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self._authenticated_url = self._build_auth_url()

    def _build_auth_url(self):
        if self.token and "github.com" in self.repo_url:
            return self.repo_url.replace(
                "https://", f"https://{self.token}:x-oauth-basic@"
            )
        return self.repo_url

    def clone_or_fetch(self):
        from .local import LocalConnector

        connector = LocalConnector(self._authenticated_url, self.local_path, self.branch)
        return connector.clone_or_fetch()

    def get_branches(self):
        from .local import LocalConnector

        connector = LocalConnector(self._authenticated_url, self.local_path, self.branch)
        return connector.get_branches()

    def get_commit_history(self, since=None):
        from .local import LocalConnector

        connector = LocalConnector(self._authenticated_url, self.local_path, self.branch)
        return connector.get_commit_history(since)

    def get_file_list(self):
        from .local import LocalConnector

        connector = LocalConnector(self._authenticated_url, self.local_path, self.branch)
        return connector.get_file_list()

    def get_file_content(self, file_path):
        from .local import LocalConnector

        connector = LocalConnector(self._authenticated_url, self.local_path, self.branch)
        return connector.get_file_content(file_path)

    def get_last_commit_for_file(self, file_path):
        from .local import LocalConnector

        connector = LocalConnector(self._authenticated_url, self.local_path, self.branch)
        return connector.get_last_commit_for_file(file_path)

    def get_owner_hint(self, file_path, commits):
        return BaseConnector.get_owner_hint(file_path, commits)
