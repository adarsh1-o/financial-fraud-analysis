import pandas as pd

from src.analytics import filter_transactions, grouped_fraud, high_value_fraud, kpis
from src.data_loader import load_transactions
from src.ai_assistant import answer_question, explain, test_gemini_connection as gemini_connection_test


def sample():
    return pd.DataFrame({"Transaction_ID":["a","b","c"],"Fraud_Status":["Fraud","Legitimate","Fraud"],"_is_fraud":[True,False,True],"Amount":[100.0,20.0,None],"Risk_Score":[90,10,50],"Payment_Method":["UPI","Card","UPI"],"City":["X","X",None]})


def test_kpis_and_missing_amount():
    result=kpis(sample())
    assert result["transactions"] == 3 and result["fraud_count"] == 2
    assert result["fraud_pct"] == 100*2/3 and result["fraud_labelled_amount"] == 100


def test_group_counts_and_amounts():
    result=grouped_fraud(sample(),"Payment_Method")
    assert result.iloc[0]["Payment_Method"] == "UPI"
    assert result.iloc[0]["fraud_count"] == 2 and result.iloc[0]["fraud_amount"] == 100


def test_filters_combine_and_empty():
    df=sample()
    assert len(filter_transactions(df,{"City":"X","Fraud_Status":"Fraud"})) == 1
    assert filter_transactions(df,{"City":"missing"}).empty


def test_high_value_and_unsupported_question():
    df=sample()
    assert high_value_fraud(df,50)["Transaction_ID"].tolist() == ["a"]
    response=answer_question("What is the weather?",df)
    assert response["supported"] is False


def test_loader_removes_only_exact_duplicates(tmp_path):
    source=pd.DataFrame({"Transaction_ID":["a","a","b"],"Fraud_Status":["Fraud","Fraud","Legitimate"],"Amount":[1,1,-2]})
    path=tmp_path/"data.csv"; source.to_csv(path,index=False)
    loaded,meta=load_transactions(path)
    assert len(loaded)==2 and meta["exact_duplicates_removed"]==1
    assert pd.isna(loaded.loc[loaded.Transaction_ID=="b","Amount"]).all()


def test_missing_required_column_fails(tmp_path):
    path=tmp_path/"bad.csv"; pd.DataFrame({"Amount":[1]}).to_csv(path,index=False)
    try:
        load_transactions(path)
    except ValueError as exc:
        assert "Fraud_Status" in str(exc)
    else:
        raise AssertionError("Expected validation error")


def test_missing_credentials_keeps_calculations_available(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response=answer_question("fraud counts by payment method",sample())
    assert response["supported"] is True
    assert "API key missing" in response["explanation"]
    assert response["results"]


def test_api_failure_is_graceful():
    class Broken:
        class Interactions:
            @staticmethod
            def create(**kwargs):
                raise TimeoutError("timeout")
        interactions=Interactions()
    result=explain("question",{"k":1},api_key="test",client=Broken())
    assert "timeout" in result


def test_ai_router_extracts_threshold():
    result=answer_question("How many fraud transactions are above 50?",sample(),api_key=None)
    assert result["supported"] and result["threshold"] == 50
    assert result["count"] == 1


def test_ai_numeric_claims_are_suppressed():
    class Numeric:
        class Interactions:
            @staticmethod
            def create(**kwargs):
                from types import SimpleNamespace
                return SimpleNamespace(output_text="There are 999 fraud cases.")
        interactions=Interactions()
    result=explain("question", {"count": 2}, api_key="test", client=Numeric())
    assert "numeric figures" in result


def test_connection_reports_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result=gemini_connection_test()
    assert result["status"]=="missing_key"


def test_connection_reports_success_with_usable_response(monkeypatch):
    from types import SimpleNamespace
    class Interactions:
        @staticmethod
        def create(**kwargs):
            return SimpleNamespace(output_text="READY")
    class Client:
        interactions=Interactions()
    monkeypatch.setattr("src.ai_assistant.get_gemini_client", lambda key: Client())
    result=gemini_connection_test("fake-test-key")
    assert result["status"]=="verified"


def test_connection_classifies_quota_errors(monkeypatch):
    class QuotaError(Exception):
        code=429
    class Interactions:
        @staticmethod
        def create(**kwargs):
            raise QuotaError("resource exhausted")
    class Client:
        interactions=Interactions()
    monkeypatch.setattr("src.ai_assistant.get_gemini_client", lambda key: Client())
    result=gemini_connection_test("fake-test-key")
    assert result["status"]=="quota_exceeded"


def test_connection_classifies_auth_errors(monkeypatch):
    class AuthError(Exception):
        code=401
    class Interactions:
        @staticmethod
        def create(**kwargs):
            raise AuthError("not authorized")
    class Client:
        interactions=Interactions()
    monkeypatch.setattr("src.ai_assistant.get_gemini_client", lambda key: Client())
    result=gemini_connection_test("fake-test-key")
    assert result["status"]=="authentication_failed"



def test_connection_classifies_sdk_permission_error(monkeypatch):
    class PermissionDeniedError(Exception):
        pass
    class Interactions:
        @staticmethod
        def create(**kwargs):
            raise PermissionDeniedError("permission denied")
    class Client:
        interactions=Interactions()
    monkeypatch.setattr("src.ai_assistant.get_gemini_client", lambda key: Client())
    result=gemini_connection_test("fake-test-key")
    assert result["status"]=="authentication_failed"
