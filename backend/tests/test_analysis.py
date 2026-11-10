from uuid import uuid4

CRITERIA_KEYS = {
    "section_completeness",
    "description_quality",
    "ats_readability",
    "skills_relevance",
    "format_length",
}


def upload_cv(upload_file, headers) -> dict:
    response = upload_file(headers, "indonesian.pdf")
    assert response.status_code == 201
    return response.json()


def create_analysis(client, headers, cv_id):
    return client.post(f"/analysis/{cv_id}", headers=headers)


def test_create_analysis_returns_full_breakdown(
    client, auth_headers, upload_file
):
    upload = upload_cv(upload_file, auth_headers)

    response = create_analysis(client, auth_headers, upload["cv"]["id"])

    assert response.status_code == 201
    body = response.json()
    assert 0 <= body["total_score"] <= 100
    breakdown = body["score_breakdown"]
    assert breakdown["version"] == 1
    assert breakdown["total_score"] == body["total_score"]
    assert len(breakdown["criteria"]) == 5
    assert {item["key"] for item in breakdown["criteria"]} == CRITERIA_KEYS
    assert sum(item["max_score"] for item in breakdown["criteria"]) == 100
    assert all(item["reasons"] for item in breakdown["criteria"])
    assert body["suggestions"]["source"] == "fallback"
    assert 3 <= len(body["suggestions"]["items"]) <= 5


def test_get_analysis_returns_saved_result(client, auth_headers, upload_file):
    upload = upload_cv(upload_file, auth_headers)
    created = create_analysis(client, auth_headers, upload["cv"]["id"]).json()

    response = client.get(f"/analysis/{created['id']}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["total_score"] == created["total_score"]
    assert body["score_breakdown"] == created["score_breakdown"]
    assert body["suggestions"] == created["suggestions"]


def test_rerun_creates_new_analysis(client, auth_headers, upload_file):
    upload = upload_cv(upload_file, auth_headers)

    first = create_analysis(client, auth_headers, upload["cv"]["id"]).json()
    second = create_analysis(client, auth_headers, upload["cv"]["id"]).json()

    assert first["id"] != second["id"]
    assert (
        client.get(f"/analysis/{first['id']}", headers=auth_headers).status_code
        == 200
    )
    assert (
        client.get(f"/analysis/{second['id']}", headers=auth_headers).status_code
        == 200
    )


def test_rerun_after_profile_correction_reflects_changes(
    client, auth_headers, upload_file
):
    upload = upload_cv(upload_file, auth_headers)
    profile_id = upload["profile"]["id"]
    first = create_analysis(client, auth_headers, upload["cv"]["id"]).json()

    update = client.put(
        f"/profile/{profile_id}", headers=auth_headers, json={"skills": []}
    )
    assert update.status_code == 200

    second = create_analysis(client, auth_headers, upload["cv"]["id"]).json()

    assert second["id"] != first["id"]
    skills = {
        item["key"]: item
        for item in second["score_breakdown"]["criteria"]
    }["skills_relevance"]
    assert skills["score"] == 0
    assert second["total_score"] <= first["total_score"]


def test_user_b_cannot_create_analysis_for_user_a_cv(
    client, auth_headers, auth_headers_factory, upload_file
):
    upload = upload_cv(upload_file, auth_headers)
    other_headers = auth_headers_factory("other@example.com")

    response = create_analysis(client, other_headers, upload["cv"]["id"])

    assert response.status_code == 404


def test_user_b_cannot_read_user_a_analysis(
    client, auth_headers, auth_headers_factory, upload_file
):
    upload = upload_cv(upload_file, auth_headers)
    analysis = create_analysis(client, auth_headers, upload["cv"]["id"]).json()
    other_headers = auth_headers_factory("other@example.com")

    response = client.get(f"/analysis/{analysis['id']}", headers=other_headers)

    assert response.status_code == 404


def test_analysis_requires_authentication(client, upload_file):
    response = create_analysis(client, {}, uuid4())

    assert response.status_code == 401


def test_unknown_cv_and_analysis_return_404(client, auth_headers):
    assert create_analysis(client, auth_headers, uuid4()).status_code == 404
    assert (
        client.get(f"/analysis/{uuid4()}", headers=auth_headers).status_code
        == 404
    )


def test_deleting_cv_removes_analyses(
    client, auth_headers, upload_file
):
    upload = upload_cv(upload_file, auth_headers)
    analysis = create_analysis(client, auth_headers, upload["cv"]["id"]).json()

    deleted = client.delete(f"/cv/{upload['cv']['id']}", headers=auth_headers)
    assert deleted.status_code == 204

    response = client.get(f"/analysis/{analysis['id']}", headers=auth_headers)
    assert response.status_code == 404
