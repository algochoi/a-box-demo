#!/usr/bin/env python3

import json

from pyteal import (
    abi,
    App,
    Approve,
    BareCallActions,
    Bytes,
    CallConfig,
    Expr,
    Int,
    Itob,
    Log,
    OnCompleteAction,
    Router,
    Seq,
    pragma,
)

pragma(compiler_version="^0.21.0")

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
        Log(Itob(App.box_create(Bytes("BoxA"), Int(44)))),
    )


@router.method(no_op=CallConfig.CALL)
def put(value: abi.String) -> Expr:
    """Write to a box"""
    return Seq(
        # box created with box_put
        App.box_put(Bytes("BoxA"), value.get()),
        Approve(),
    )


@router.method(no_op=CallConfig.CALL)
def read() -> Expr:
    """Read from a box"""
    return Seq(
        # App.box_put(Bytes("BoxA"), Bytes("Let's read some bytes")),
        boxint := App.box_get(Bytes("BoxA")),
        Log(boxint.value()),
    )


@router.method(no_op=CallConfig.CALL)
def length() -> Expr:
    """Get the length a box value"""
    return Seq(
        # App.box_put(
        #     Bytes("BoxA"), Bytes("this is a test of a very very very very long string")
        # ),
        bt := App.box_length(Bytes("BoxA")),
        Log(Itob(bt.value())),
    )


@router.method(no_op=CallConfig.CALL)
def delete() -> Expr:
    """Delete a box"""
    return Seq(
        # App.box_put(
        #     Bytes("BoxA"), Bytes("this is a test of a very very very very long string")
        # ),
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
