#!/usr/bin/env python3

import base64

from algosdk import abi, atomic_transaction_composer, logic
from algosdk.future import transaction
from algosdk.v2client import algod

import sandbox_utils as sb

sb_account = sb.SandboxAccount()
client = sb.create_algod_client()


def compile_program(client: algod.AlgodClient, source_code: bytes) -> bytes:
    compile_response = client.compile(source_code.decode("utf-8"))
    return base64.b64decode(compile_response["result"])


# Decodes a logged transaction response
def decode_return_value(log, isInt=False):
    if log:
        if isInt:
            return [int.from_bytes(base64.b64decode(s), "big") for s in log]
        return [base64.b64decode(s).decode() for s in log]


# Creates an app and returns the app ID
def create_test_app() -> int:
    # Declare application state storage (immutable)
    local_ints = 1
    local_bytes = 1
    global_ints = 1
    global_bytes = 1

    # Define app schema
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)
    on_complete = transaction.OnComplete.NoOpOC.real

    # Compile the program with algod
    source_code = b""
    clear_code = b""
    with open("approve-box.teal", mode="rb") as file:
        source_code = file.read()
    with open("clear-box.teal", mode="rb") as file:
        clear_code = file.read()
    source_program = compile_program(client, source_code)
    clear_program = compile_program(client, clear_code)

    # Prepare the transaction
    params = client.suggested_params()

    private_key, sender = sb_account.get_funded_transient(client)

    # Create an unsigned transaction
    txn = transaction.ApplicationCreateTxn(
        sender,
        params,
        on_complete,
        source_program,
        clear_program,
        global_schema,
        local_schema,
    )

    # Sign transaction with funded private key
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # Send transaction
    client.send_transactions([signed_txn])

    transaction_response = transaction.wait_for_confirmation(client, tx_id, 5)
    # print(transaction_response)
    app_id = transaction_response["application-index"]
    algod_response = client.application_info(app_id)
    # print(algod_response)
    return app_id


def fund_program(app_id: int):
    private_key, sender = sb_account.get_funded_transient(client)
    # Send transaction to fund the app.
    txn = transaction.PaymentTxn(
        sender,
        client.suggested_params(),
        logic.get_application_address(app_id),
        5_000_000,
    )

    # Sign transaction with funded private key
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # Send transaction
    client.send_transactions([signed_txn])
    _ = transaction.wait_for_confirmation(client, tx_id, 5)


def call_box_method(app_id: int, method: abi.Method, box_ref: bytes, args=None):
    private_key, sender = sb_account.get_funded_transient(client)
    # Initialize ATC to call ABI methods
    atc = atomic_transaction_composer.AtomicTransactionComposer()
    transaction_signer = atomic_transaction_composer.AccountTransactionSigner(
        private_key
    )

    atc.add_method_call(
        app_id,
        method,
        sender,
        client.suggested_params(),
        transaction_signer,
        method_args=args if args else [],
        boxes=[
            (0, box_ref)
        ],  # For the Python SDK, provide a list of (app_id, box_key) tuples you want to access.
    )
    resp = atc.execute(client, 5)
    info = client.pending_transaction_info(resp.tx_ids[0])
    print(f"Box Txn Info: {info}")

    # Decoded the returned output and print
    if "logs" in info:
        return info["logs"]


def create_box(app_id: int):
    create_method = abi.Method.from_signature("create()void")
    print(">> Creating a box...")
    box_return = call_box_method(app_id, create_method, b"BoxA")
    print(f"Create box: {decode_return_value(box_return, isInt=True)}\n")


def put_box(app_id: int):
    put_method = abi.Method.from_signature("put(string)void")
    print(">> Write into a box...")
    box_return = call_box_method(
        app_id, put_method, b"BoxA", ["The quick brown fox jumps over the lazy dog."]
    )
    print(f"Returned box: {decode_return_value(box_return)}\n")


def read_box(app_id: int):
    read_method = abi.Method.from_signature("read()void")
    print(">> Read from a box...")
    box_return = call_box_method(app_id, read_method, b"BoxA")
    print(f"Returned box: {decode_return_value(box_return)}\n")


def length_box(app_id: int):
    length_method = abi.Method.from_signature("length()void")
    print(">> Get the length of a box...")
    box_return = call_box_method(app_id, length_method, b"BoxA")
    print(f"Length decoded {decode_return_value(box_return, isInt=True)}\n")


def delete_box(app_id: int):
    delete_method = abi.Method.from_signature("delete()void")
    print(">> Deleting a box...")
    box_return = call_box_method(app_id, delete_method, b"BoxA")
    print(f"Delete box success: {decode_return_value(box_return, isInt=True)}\n")


if __name__ == "__main__":
    id = create_test_app()
    fund_program(id)
    create_box(id)
    put_box(id)
    read_box(id)
    length_box(id)
    delete_box(id)
