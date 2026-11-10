from uuid import uuid4


def test_get_profile_returns_owner_data(client, auth_headers, upload_file):
    upload = upload_file(auth_headers, "indonesian.pdf").json()

    response = client.get(
        f"/profile/{upload['profile']['id']}", headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "RIZKY PRATAMA"
    assert body["original_filename"] == "indonesian.pdf"
    assert body["skills"]


def test_user_b_cannot_read_user_a_profile(
    client, auth_headers, auth_headers_factory, upload_file
):
    upload = upload_file(auth_headers, "indonesian.pdf").json()
    other_headers = auth_headers_factory("other@example.com")

    response = client.get(
        f"/profile/{upload['profile']['id']}", headers=other_headers
    )

    assert response.status_code == 404


def test_user_b_cannot_update_user_a_profile(
    client, auth_headers, auth_headers_factory, upload_file
):
    upload = upload_file(auth_headers, "indonesian.pdf").json()
    other_headers = auth_headers_factory("other@example.com")

    response = client.put(
        f"/profile/{upload['profile']['id']}",
        headers=other_headers,
        json={"name": "Penyusup"},
    )

    assert response.status_code == 404


def test_unknown_profile_returns_404(client, auth_headers):
    response = client.get(f"/profile/{uuid4()}", headers=auth_headers)

    assert response.status_code == 404


def test_update_profile_persists_corrections(client, auth_headers, upload_file):
    upload = upload_file(auth_headers, "indonesian.pdf").json()
    profile_id = upload["profile"]["id"]

    payload = {
        "name": "Rizky Pratama",
        "email": "rizky.baru@example.com",
        "phone": "+62 811 2222 3333",
        "summary": "Ringkasan yang sudah dikoreksi.",
        "links": {
            "github": "https://github.com/rizkybaru",
            "linkedin": "",
            "other": ["https://portofolio.dev/rizky"],
        },
        "education": [
            {
                "institution": "Universitas Indonesia",
                "degree": "S1 Ilmu Komputer",
                "period": "2016 - 2020",
                "details": ["IPK 3.7"],
            }
        ],
        "experience": [
            {
                "role": "Senior Backend Engineer",
                "company": "PT Teknologi Nusantara",
                "period": "2021 - Sekarang",
                "details": ["Memimpin 3 engineer"],
            }
        ],
        "projects": [
            {
                "name": "CareerLens API",
                "period": "2023",
                "description": "API analisis CV",
            }
        ],
        "skills": [
            {"name": "js"},
            {"name": "go"},
            {"name": "Custom Tool", "category": "Tools"},
        ],
    }

    response = client.put(
        f"/profile/{profile_id}", headers=auth_headers, json=payload
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Rizky Pratama"
    assert body["email"] == "rizky.baru@example.com"
    assert body["links"]["github"] == "https://github.com/rizkybaru"
    assert body["links"]["linkedin"] is None
    assert body["links"]["other"] == ["https://portofolio.dev/rizky"]
    assert body["education"][0]["details"] == ["IPK 3.7"]
    assert body["experience"][0]["role"] == "Senior Backend Engineer"
    assert body["projects"][0]["description"] == "API analisis CV"
    assert {skill["name"] for skill in body["skills"]} == {
        "JavaScript",
        "Go",
        "Custom Tool",
    }

    fetched = client.get(f"/profile/{profile_id}", headers=auth_headers).json()
    assert fetched["name"] == "Rizky Pratama"
    assert {skill["name"] for skill in fetched["skills"]} == {
        "JavaScript",
        "Go",
        "Custom Tool",
    }


def test_update_profile_can_clear_skills(client, auth_headers, upload_file):
    upload = upload_file(auth_headers, "indonesian.pdf").json()
    profile_id = upload["profile"]["id"]
    assert upload["profile"]["skills"]

    response = client.put(
        f"/profile/{profile_id}", headers=auth_headers, json={"skills": []}
    )

    assert response.status_code == 200
    assert response.json()["skills"] == []


def test_update_profile_rejects_invalid_email(
    client, auth_headers, upload_file
):
    upload = upload_file(auth_headers, "indonesian.pdf").json()

    response = client.put(
        f"/profile/{upload['profile']['id']}",
        headers=auth_headers,
        json={"email": "bukan-email"},
    )

    assert response.status_code == 422


def test_update_profile_accepts_blank_optional_fields(
    client, auth_headers, upload_file
):
    upload = upload_file(auth_headers, "indonesian.pdf").json()

    response = client.put(
        f"/profile/{upload['profile']['id']}",
        headers=auth_headers,
        json={"email": "", "phone": "", "name": ""},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] is None
    assert body["phone"] is None
    assert body["name"] is None
