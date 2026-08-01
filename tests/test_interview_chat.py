from app import interviewer_intro, is_greeting


def test_greeting_detection_accepts_common_greetings():
    assert is_greeting("Hi!")
    assert is_greeting("good morning")
    assert not is_greeting("I have experience with Python and SQL")


def test_introduction_uses_interview_context():
    intro = interviewer_intro(
        {
            "role": "Backend Engineer",
            "company": "JP Morgan",
            "match": {"required_skills": ["python", "sql"]},
        }
    )
    assert "Backend Engineer" in intro
    assert "JP Morgan" in intro
    assert "python, sql" in intro
