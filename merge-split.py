from dotenv import load_dotenv
from dataclasses import dataclass
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware

load_dotenv()


NegRiskAdapterABI = """[{"inputs":[{"internalType":"bytes32","name":"_conditionId","type":"bytes32"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"splitPosition","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_conditionId","type":"bytes32"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"mergePositions","outputs":[],"stateMutability":"nonpayable","type":"function"}]"""
ConditionalTokenABI = """[{"constant":"false","inputs":[{"name":"collateralToken","type":"address"},{"name":"parentCollectionId","type":"bytes32"},{"name":"CONDITION_ID","type":"bytes32"},{"name":"partition","type":"uint256[]"},{"name":"amount","type":"uint256"}],"name":"splitPosition","outputs":[],"payable":"false","stateMutability":"nonpayable","type":"function"},{"constant":"false","inputs":[{"name":"collateralToken","type":"address"},{"name":"parentCollectionId","type":"bytes32"},{"name":"CONDITION_ID","type":"bytes32"},{"name":"partition","type":"uint256[]"},{"name":"amount","type":"uint256"}],"name":"mergePositions","outputs":[],"payable":"false","stateMutability":"nonpayable","type":"function"}]"""


@dataclass
class ContractConfig:
    neg_risk_adapter: str
    conditional_tokens: str
    collateral: str


def get_contract_config(chainID: int) -> ContractConfig:
    """
    Get the contract configuration for the chain
    """

    CONFIG = {
        137: ContractConfig(
            neg_risk_adapter="0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296",
            collateral="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            conditional_tokens="0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",
        ),
        80002: ContractConfig(
            neg_risk_adapter="",
            collateral="0x9c4e1703476e875070ee25b56a58b008cfb8fa78",
            conditional_tokens="0x69308FB512518e39F9b16112fA8d994F4e2Bf8bB",
        ),
    }

    return CONFIG.get(chainID)


# wallet
ADDRESS = os.getenv("ADDRESS")
PK = os.getenv("PK")

# RPC_URL
RPC_URL = os.getenv("RPC_URL")

# contracts
CHAIN_ID = int(os.getenv("CHAIN_ID"))
CONTRACTS = get_contract_config(CHAIN_ID)

# market
CONDITION_ID = os.getenv("CONDITION_ID")
IS_NEG_RISK_MARKET = os.getenv("IS_NEG_RISK_MARKET") == "true"


w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def main():
    neg_risk_adapter = w3.eth.contract(
        address=CONTRACTS.neg_risk_adapter, abi=NegRiskAdapterABI
    )
    conditional_tokens = w3.eth.contract(
        address=CONTRACTS.conditional_tokens, abi=ConditionalTokenABI
    )
    split_position(neg_risk_adapter, conditional_tokens)
    merge_positions(neg_risk_adapter, conditional_tokens)


def split_position(neg_risk_adapter, conditional_tokens):
    nonce = w3.eth.getTransactionCount(ADDRESS)

    if IS_NEG_RISK_MARKET:
        transaction = neg_risk_adapter.functions.splitPosition(
            CONDITION_ID, 10000000
        ).buildTransaction(
            {
                "chainId": CHAIN_ID,
                "gas": 1000000,
                "from": ADDRESS,
                "nonce": nonce,
            }
        )
    else:
        transaction = conditional_tokens.functions.splitPosition(
            CONTRACTS.collateral,
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            CONDITION_ID,
            [1, 2],
            10000000,
        ).buildTransaction(
            {
                "chainId": CHAIN_ID,
                "gas": 1000000,
                "from": ADDRESS,
                "nonce": nonce,
            }
        )

    signed_txn = w3.eth.account.signTransaction(transaction, private_key=PK)
    tx_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    tx = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    w3.eth.wait_for_transaction_receipt(tx, 600)
    print("split position " + tx_hash)


def merge_positions(neg_risk_adapter, conditional_tokens):
    nonce = w3.eth.getTransactionCount(ADDRESS)

    if IS_NEG_RISK_MARKET:
        transaction = neg_risk_adapter.functions.mergePositions(
            CONDITION_ID, 10000000
        ).buildTransaction(
            {
                "chainId": CHAIN_ID,
                "gas": 1000000,
                "from": ADDRESS,
                "nonce": nonce,
            }
        )
    else:
        transaction = conditional_tokens.functions.mergePositions(
            CONTRACTS.collateral,
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            CONDITION_ID,
            [1, 2],
            10000000,
        ).buildTransaction(
            {
                "chainId": CHAIN_ID,
                "gas": 1000000,
                "from": ADDRESS,
                "nonce": nonce,
            }
        )

    signed_txn = w3.eth.account.signTransaction(transaction, private_key=PK)
    tx_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    tx = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    w3.eth.wait_for_transaction_receipt(tx, 600)
    print("merge positions " + tx_hash)


main()
