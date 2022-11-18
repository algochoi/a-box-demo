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
def decode_return_value(resp):
    log = resp["logs"]
    return [base64.b64decode(s).decode() for s in log]


# Creates an app and returns the app ID
def create_test_app() -> int:
    # Declare application state storage (immutable)
    local_ints = 1
    local_bytes = 1
    global_ints = 1
    global_bytes = 0

    # Define app schema
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)
    on_complete = transaction.OnComplete.NoOpOC.real

    # Compile the program with algod
    source_code = ""
    clear_code = ""
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
    print(transaction_response)
    app_id = transaction_response["application-index"]
    algod_response = client.application_info(app_id)
    print(algod_response)
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


def call_program(app_id: int):
    private_key, sender = sb_account.get_funded_transient(client)
    # Initialize ATC to call ABI methods
    atc = atomic_transaction_composer.AtomicTransactionComposer()
    create_method = abi.Method.from_signature("put()void")
    read_method = abi.Method.from_signature("read()void")
    length_method = abi.Method.from_signature("length()void")
    transaction_signer = atomic_transaction_composer.AccountTransactionSigner(
        private_key
    )

    atc.add_method_call(
        app_id,
        read_method,
        sender,
        client.suggested_params(),
        transaction_signer,
        boxes=[(0, b"BoxA")],
    )
    resp = atc.execute(client, 5)
    info = client.pending_transaction_info(resp.tx_ids[0])
    print(f"Box Info: {info}")

    # Decoded the returned output and print
    return_string = decode_return_value(info)
    print(f"Returned box: {return_string}")


if __name__ == "__main__":
    id = create_test_app()
    fund_program(id)
    call_program(id)
