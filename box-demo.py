#!/usr/bin/env python3

from pyteal import (
    App,
    Approve,
    Assert,
    Balance,
    BareCallActions,
    Bytes,
    CallConfig,
    Expr,
    For,
    Ge,
    Global,
    Gt,
    If,
    InnerTxnBuilder,
    Int,
    Not,
    OnComplete,
    OnCompleteAction,
    Reject,
    Return,
    Router,
    ScratchVar,
    Seq,
    Subroutine,
    TealType,
    Txn,
    TxnField,
    TxnType,
    abi,
    pragma,
)

pragma(compiler_version="^0.20.1")

CONTRACT_VERSION = 8

router = Router(
    # Name of the contract
    "box-demo",
    # What to do for each on-complete type when no arguments are passed (bare call)
    BareCallActions(
        no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE)
    ),
)


@router.method(no_op=CallConfig.CALL)
def create() -> Expr:
    """Create a box"""
    return Seq(
        # 100 byte box created with box_create
        Assert(App.box_create(Bytes("MyKey"), Int(100)) == Int(1))
    )


@router.method(no_op=CallConfig.CALL)
def put() -> Expr:
    return Seq(
        # box created with box_put
        App.box_put(Bytes("MyKey"), Bytes("My Values")),
        Approve(),
    )


if __name__ == "__main__":
    approval, clearstate, contract = router.compile_program(version=CONTRACT_VERSION)

    with open("approve-box.teal", "w") as f:
        f.write(approval)

    with open("clear-box.teal", "w") as f:
        f.write(clearstate)
