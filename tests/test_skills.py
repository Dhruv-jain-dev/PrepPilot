from utils.skills import match_resume_to_job


def test_match_scores_shared_skills_and_identifies_gaps():
    result = match_resume_to_job("Python, SQL, Git", "Python SQL Docker")
    assert result["score"] == 67
    assert result["strong_skills"] == ["python", "sql"]
    assert result["missing_skills"] == ["docker"]
