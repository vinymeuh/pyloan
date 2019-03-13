import pytest

from pyloan.loan import Loan

testdata = [
    (
        "loan1",
        "r0",
        [
            {
                "annualRate": 2.115,
                "insurance": 1.2,
                "periods": 120,
                "principal": 10000,
                "startDate": "2010-09-15",
            }
        ],
    ),
    (
        "loan2",
        "r0",
        [
            {
                "annualRate": 2.115,
                "insurance": 1.2,
                "periods": 240,
                "principal": 100000,
                "startDate": "2010-09-15",
            },
            {
                "annualRate": 1.115,
                "insurance": 1.2,
                "periods": 120,
                "startDate": "2013-09-15",
            },
        ],
    ),
]


@pytest.mark.parametrize("name,revision,phases", testdata)
def test_loan(name, revision, phases):
    loan = Loan(name, revision, phases)
    assert loan.name == name
    assert loan.revision == revision
    assert loan.phases == phases
    assert loan.repayments == []
    assert loan.early_repayments == []
    assert loan.summary == {}
    loan.compute_repayment_plan()
    assert loan.sanity_checks() == True
