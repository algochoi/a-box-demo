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
    Itob,
    Log,
    OnCompleteAction,
    Router,
    ScratchVar,
    Seq,
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
        # 44 byte box created with box_create
        Assert(App.box_create(Bytes("BoxA"), Int(44)) == Int(1))
    )


@router.method(no_op=CallConfig.CALL)
def put() -> Expr:
    return Seq(
        # box created with box_put
        App.box_put(
            Bytes("BoxA"), Bytes("The quick brown fox jumps over the lazy dog.")
        ),
        Approve(),
    )


@router.method(no_op=CallConfig.CALL)
def read() -> Expr:
    return Seq(
        # App.box_put(Bytes("BoxA"), Bytes("Let's read some bytes")),
        boxint := App.box_get(Bytes("BoxA")),
        Assert(boxint.hasValue()),
        Log(boxint.value()),
    )


@router.method(no_op=CallConfig.CALL)
def length() -> Expr:
    return Seq(
        # App.box_put(
        #     Bytes("BoxA"), Bytes("this is a test of a very very very very long string")
        # ),
        bt := App.box_length(Bytes("BoxA")),
        Assert(bt.hasValue()),
        Log(Itob(bt.value())),
    )


@router.method(no_op=CallConfig.CALL)
def delete() -> Expr:
    output = ScratchVar()
    return Seq(
        App.box_put(
            Bytes("BoxA"), Bytes("this is a test of a very very very very long string")
        ),
        Log(Itob(App.box_delete(Bytes("BoxA")))),
    )


if __name__ == "__main__":
    approval, clearstate, contract = router.compile_program(version=CONTRACT_VERSION)

    with open("approve-box.teal", "w") as f:
        f.write(approval)

    with open("clear-box.teal", "w") as f:
        f.write(clearstate)

    with open("contract.json", "w") as f:
        f.write(json.dumps(contract.dictify(), indent=4))
