from database.mongodb import InMemoryRepository


def test_in_memory_repository_keeps_mock_interview_working_without_atlas():
    repo = InMemoryRepository()
    session_id = repo.create_session(
        "resume.pdf",
        b"pdf",
        "Python and SQL",
        "Python SQL Docker",
        "Backend Engineer",
        "General",
        {"match": {"score": 67}, "questions": ["Tell me about yourself."], "readiness": 70},
    )

    repo.add_evaluation(session_id, "Tell me about yourself.", "I build APIs.", {"score": 7.0})
    repo.add_question(session_id, "How would you test an API?")

    session = repo.get_session(session_id)
    assert session is not None
    assert "How would you test an API?" in session["questions"]
    assert repo.evaluations(session_id)[0]["score"] == 7.0
