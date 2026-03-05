import responses
from unittest.mock import patch
from discovery.resolver import _normalize, _slug_variants, resolve, KNOWN_COMPANIES


class TestNormalize:
    def test_lowercase_and_strip_spaces(self):
        assert _normalize("Factory AI") == "factoryai"

    def test_strip_punctuation(self):
        assert _normalize("Hinge Health") == "hingehealth"

    def test_already_clean(self):
        assert _normalize("stripe") == "stripe"

    def test_special_characters(self):
        assert _normalize("So-Fi!") == "sofi"

    def test_empty_string(self):
        assert _normalize("") == ""


class TestSlugVariants:
    def test_strips_ai_suffix(self):
        assert _slug_variants("factoryai") == ["factoryai", "factory"]

    def test_strips_inc_suffix(self):
        assert _slug_variants("stripeinc") == ["stripeinc", "stripe"]

    def test_strips_labs_suffix(self):
        assert _slug_variants("openlabs") == ["openlabs", "open"]

    def test_strips_hq_suffix(self):
        assert _slug_variants("linearhq") == ["linearhq", "linear"]

    def test_no_suffix_unchanged(self):
        assert _slug_variants("stripe") == ["stripe"]

    def test_does_not_strip_to_empty(self):
        assert _slug_variants("ai") == ["ai"]


class TestResolveKnownCompanies:
    def test_known_company_exact(self):
        result = resolve("stripe")
        assert result == {"ats": "greenhouse", "slug": "stripe"}

    def test_known_company_case_insensitive(self):
        result = resolve("Stripe")
        assert result == {"ats": "greenhouse", "slug": "stripe"}

    def test_known_company_with_spaces(self):
        result = resolve("Factory AI")
        assert result == {"ats": "ashby", "slug": "factory"}

    def test_known_ashby_company(self):
        result = resolve("Notion")
        assert result == {"ats": "ashby", "slug": "notion"}


class TestResolveProbing:
    @responses.activate
    def test_probe_with_suffix_stripping(self):
        """'Factory AI' normalizes to 'factoryai', which 404s, but 'factory' succeeds."""
        responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/factoryai/jobs", status=404)
        responses.add(responses.GET, "https://api.lever.co/v0/postings/factoryai", status=404)
        responses.add(responses.GET, "https://api.ashbyhq.com/posting-api/job-board/factoryai", status=404)
        responses.add(responses.GET, "https://api.gem.com/job_board/v0/factoryai/job_posts/", status=404)
        responses.add(responses.POST, "https://apply.workable.com/api/v3/accounts/factoryai/jobs", json={"total": 0, "results": []}, status=200)
        responses.add(responses.GET, "https://api.smartrecruiters.com/v1/companies/factoryai/postings", status=404)
        # factory (suffix-stripped) hits on Ashby
        responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/factory/jobs", status=404)
        responses.add(responses.GET, "https://api.lever.co/v0/postings/factory", status=404)
        responses.add(responses.GET, "https://api.ashbyhq.com/posting-api/job-board/factory", json={"jobs": []}, status=200)
        # Note: known_companies.json already has "factoryai", so this test uses a mock
        # to bypass that. We test the probing path directly.
        with patch.dict("discovery.resolver.KNOWN_COMPANIES", {}, clear=True):
            result = resolve("Factory AI")
        assert result == {"ats": "ashby", "slug": "factory"}

    @responses.activate
    def test_probe_greenhouse_success(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/testcorp/jobs",
            json={"jobs": []},
            status=200,
        )
        result = resolve("testcorp")
        assert result == {"ats": "greenhouse", "slug": "testcorp"}

    @responses.activate
    def test_probe_lever_success(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/levercorp/jobs",
            status=404,
        )
        responses.add(
            responses.GET,
            "https://api.lever.co/v0/postings/levercorp",
            json=[],
            status=200,
        )
        result = resolve("levercorp")
        assert result == {"ats": "lever", "slug": "levercorp"}

    @responses.activate
    def test_probe_ashby_success(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/ashbycorp/jobs",
            status=404,
        )
        responses.add(
            responses.GET,
            "https://api.lever.co/v0/postings/ashbycorp",
            status=404,
        )
        responses.add(
            responses.GET,
            "https://api.ashbyhq.com/posting-api/job-board/ashbycorp",
            json={"jobs": []},
            status=200,
        )
        result = resolve("ashbycorp")
        assert result == {"ats": "ashby", "slug": "ashbycorp"}

    @responses.activate
    def test_probe_gem_success(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/gemcorp/jobs",
            status=404,
        )
        responses.add(
            responses.GET,
            "https://api.lever.co/v0/postings/gemcorp",
            status=404,
        )
        responses.add(
            responses.GET,
            "https://api.ashbyhq.com/posting-api/job-board/gemcorp",
            status=404,
        )
        responses.add(
            responses.GET,
            "https://api.gem.com/job_board/v0/gemcorp/job_posts/",
            json=[],
            status=200,
        )
        result = resolve("gemcorp")
        assert result == {"ats": "gem", "slug": "gemcorp"}

    @responses.activate
    def test_probe_workable_success(self):
        responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/wkcorp/jobs", status=404)
        responses.add(responses.GET, "https://api.lever.co/v0/postings/wkcorp", status=404)
        responses.add(responses.GET, "https://api.ashbyhq.com/posting-api/job-board/wkcorp", status=404)
        responses.add(responses.GET, "https://api.gem.com/job_board/v0/wkcorp/job_posts/", status=404)
        responses.add(
            responses.POST,
            "https://apply.workable.com/api/v3/accounts/wkcorp/jobs",
            json={"total": 5, "results": []},
            status=200,
        )
        result = resolve("wkcorp")
        assert result == {"ats": "workable", "slug": "wkcorp"}

    @responses.activate
    def test_probe_smartrecruiters_success(self):
        responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/srcorp/jobs", status=404)
        responses.add(responses.GET, "https://api.lever.co/v0/postings/srcorp", status=404)
        responses.add(responses.GET, "https://api.ashbyhq.com/posting-api/job-board/srcorp", status=404)
        responses.add(responses.GET, "https://api.gem.com/job_board/v0/srcorp/job_posts/", status=404)
        responses.add(responses.POST, "https://apply.workable.com/api/v3/accounts/srcorp/jobs", json={"total": 0, "results": []}, status=200)
        responses.add(
            responses.GET,
            "https://api.smartrecruiters.com/v1/companies/srcorp/postings",
            json={"content": []},
            status=200,
        )
        result = resolve("srcorp")
        assert result == {"ats": "smartrecruiters", "slug": "srcorp"}

    @responses.activate
    @patch("discovery.resolver._probe_workday", return_value=None)
    def test_probe_all_fail_returns_none(self, mock_wd):
        responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/unknowncorp/jobs", status=404)
        responses.add(responses.GET, "https://api.lever.co/v0/postings/unknowncorp", status=404)
        responses.add(responses.GET, "https://api.ashbyhq.com/posting-api/job-board/unknowncorp", status=404)
        responses.add(responses.GET, "https://api.gem.com/job_board/v0/unknowncorp/job_posts/", status=404)
        responses.add(responses.POST, "https://apply.workable.com/api/v3/accounts/unknowncorp/jobs", json={"total": 0, "results": []}, status=200)
        responses.add(responses.GET, "https://api.smartrecruiters.com/v1/companies/unknowncorp/postings", status=404)
        result = resolve("unknowncorp")
        assert result is None

    @patch("discovery.resolver._probe_workday")
    @responses.activate
    def test_probe_workday_success(self, mock_wd):
        responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/somecorp/jobs", status=404)
        responses.add(responses.GET, "https://api.lever.co/v0/postings/somecorp", status=404)
        responses.add(responses.GET, "https://api.ashbyhq.com/posting-api/job-board/somecorp", status=404)
        responses.add(responses.GET, "https://api.gem.com/job_board/v0/somecorp/job_posts/", status=404)
        responses.add(responses.POST, "https://apply.workable.com/api/v3/accounts/somecorp/jobs", json={"total": 0, "results": []}, status=200)
        responses.add(responses.GET, "https://api.smartrecruiters.com/v1/companies/somecorp/postings", status=404)
        mock_wd.return_value = {
            "ats": "workday",
            "slug": "somecorp",
            "base_url": "https://somecorp.wd3.myworkdayjobs.com",
            "board_name": "Somecorp",
        }
        result = resolve("somecorp")
        assert result["ats"] == "workday"
        assert result["base_url"] == "https://somecorp.wd3.myworkdayjobs.com"
