#!/usr/bin/env python3

import json

from pyteal import (
    App,
    Approve,
    Assert,
    BareCallActions,
    Bytes,
    CallConfig,
    Expr,
    Int,
    OnComplete,
    OnCompleteAction,
    Router,
    ScratchVar,
    Seq,
    Subroutine,
    TealType,
    Txn,
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
        Assert(App.box_create(Bytes("CreateMyKey"), Int(100)) == Int(1))
    )


@router.method(no_op=CallConfig.CALL)
def put() -> Expr:
    return Seq(
        # box created with box_put
        App.box_put(Bytes("PutMyKey"), Bytes("My Values")),
        Approve(),
    )


@router.method(no_op=CallConfig.CALL)
def read() -> Expr:
    return Seq(
        App.box_put(Bytes("Cnt"), Bytes("Let's read some bytes")),
        boxint := App.box_get(Bytes("Cnt")),
        Assert(boxint.hasValue()),
    )


@router.method(no_op=CallConfig.CALL)
def length() -> Expr:
    return Seq(
        App.box_put(
            Bytes("BoxA"), Bytes("this is a test of a very very very very long string")
        ),
        bt := App.box_length(Bytes("BoxA")),
        Assert(bt.hasValue()),
    )


if __name__ == "__main__":
    approval, clearstate, contract = router.compile_program(version=CONTRACT_VERSION)

    with open("approve-box.teal", "w") as f:
        f.write(approval)

    with open("clear-box.teal", "w") as f:
        f.write(clearstate)

    with open("contract.json", "w") as f:
        f.write(json.dumps(contract.dictify(), indent=4))
