import re
from collections import Counter
from datetime import datetime

import numpy as np


class CommitClassifier:
    RULE_CATEGORIES = {
        "bug_fix": [
            r"\bfix(?:ed|es)?\b",
            r"\bbug\b",
            r"\bpatch\b",
            r"\bhotfix\b",
            r"\bresolve[sd]?\b",
            r"\bcorrect(?:ed|s)?\b",
            r"\berror\b",
            r"\bcrash\b",
            r"\bissue\b",
        ],
        "feature": [
            r"\badd(?:ed|s)?\b",
            r"\bnew\b",
            r"\bfeature\b",
            r"\bimplement(?:ed|s)?\b",
            r"\bcreate[d]?\b",
            r"\bintroduce[d]?\b",
            r"\bsupport[s]?\s+for\b",
            r"\benable\b",
        ],
        "refactoring": [
            r"\brefactor(?:ed|s|ing)?\b",
            r"\bclean\s*up\b",
            r"\bcleanup\b",
            r"\bsimplify\b",
            r"\brename[d]?\b",
            r"\breorganize[d]?\b",
            r"\brestructur(?:ed?|ing)\b",
            r"\bpolish\b",
            r"\bimprove\b",
            r"\boptimize\b",
        ],
        "documentation": [
            r"\bdoc(?:s|umentation)?\b",
            r"\breadme\b",
            r"\bcomment[s]?\b",
            r"\bmanual\b",
            r"\bwiki\b",
            r"\bchangelog\b",
            r"\blicense\b",
        ],
        "test": [
            r"\btest(?:s|ing|ed)?\b",
            r"\bspec\b",
            r"\bcoverage\b",
            r"\bassert\b",
            r"\bmock\b",
            r"\bstub\b",
            r"\bfixture\b",
        ],
        "build_config": [
            r"\bbuild\b",
            r"\bci\b",
            r"\bdeploy\b",
            r"\bdocker\b",
            r"\bconfig(?:uration)?\b",
            r"\bsetup\b",
            r"\binstall\b",
            r"\bdependency\b",
            r"\bversion\b",
            r"\bupgrade\b",
            r"\brelease\b",
            r"\bpackage\b",
            r"\bnpm\b",
            r"\bpip\b",
            r"\bmaven\b",
            r"\bgradle\b",
            r"\bmakefile\b",
            r"\bcmake\b",
        ],
    }

    def __init__(self):
        self._vectorizer = None
        self._cluster_model = None
        self._classifier = None
        self._cluster_labels = {}
        self._labeled_count = 0
        self._use_supervised = False
        self._labels_mapping = {}

    def classify_rule_based(self, message):
        message_lower = message.lower()
        best_category = "other"
        best_score = 0

        for category, patterns in self.RULE_CATEGORIES.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            if score > best_score:
                best_score = score
                best_category = category

        return best_category

    def classify_batch(self, messages):
        results = []
        for msg in messages:
            results.append(self.classify_rule_based(msg))
        return results

    def cluster_unsupervised(self, messages):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans

        if len(messages) < 5:
            return [self.classify_rule_based(m) for m in messages]

        try:
            self._vectorizer = TfidfVectorizer(
                max_features=500, stop_words="english", ngram_range=(1, 2)
            )
            X = self._vectorizer.fit_transform(messages)

            n_clusters = min(max(3, len(messages) // 10), 8)
            self._cluster_model = KMeans(
                n_clusters=n_clusters, random_state=42, n_init=10
            )
            cluster_labels = self._cluster_model.fit_predict(X)

            cluster_terms = self._get_cluster_terms(X, cluster_labels, n_clusters)
            labels = []
            for label in cluster_labels:
                labels.append(f"cluster_{label}")
            return labels, cluster_terms
        except Exception:
            return [self.classify_rule_based(m) for m in messages], {}

    def _get_cluster_terms(self, X, labels, n_clusters):
        terms = {}
        feature_names = self._vectorizer.get_feature_names_out()
        for i in range(n_clusters):
            cluster_docs = X[labels == i]
            if cluster_docs.shape[0] > 0:
                centroid = cluster_docs.mean(axis=0).A1
                top_indices = centroid.argsort()[-5:][::-1]
                top_terms = [feature_names[j] for j in top_indices]
                terms[f"cluster_{i}"] = top_terms
        return terms

    def transition_to_supervised(self, messages, labels):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB

        if len(set(labels)) < 2 or len(messages) < 10:
            return False

        try:
            self._vectorizer = TfidfVectorizer(
                max_features=500, stop_words="english", ngram_range=(1, 2)
            )
            X = self._vectorizer.fit_transform(messages)
            self._classifier = MultinomialNB()
            self._classifier.fit(X, labels)
            self._use_supervised = True
            self._labeled_count = len(messages)
            return True
        except Exception:
            return False

    def predict(self, messages):
        if self._use_supervised and self._classifier and self._vectorizer:
            try:
                X = self._vectorizer.transform(messages)
                predictions = self._classifier.predict(X)
                return list(predictions)
            except Exception:
                pass
        return [self.classify_rule_based(m) for m in messages]

    @property
    def is_supervised_ready(self):
        return self._use_supervised

    @property
    def training_sample_count(self):
        return self._labeled_count
