from web3 import Web3, HTTPProvider, Account
from web3.auto import w3

import json, random, time
from loguru import logger

with open('settings.json', 'r', encoding='utf-8-sig') as file:
    file_list: dict = json.load(file)

value_from = float(file_list['BridgeConfig']['amount_from'])
value_to = float(file_list['BridgeConfig']['amount_to'])

value = w3.to_wei(random.uniform(value_from, value_to), 'ether')

eth_w3 = Web3(Web3.HTTPProvider("https://eth.llamarpc.com"))
contract_address_eth = "0x1a0ad011913A150f69f6A19DF447A0CfD9551054"
contract_abi_eth = json.load(open('./abis/abi.json'))
bridger_contract = eth_w3.eth.contract(contract_address_eth, abi=contract_abi_eth)

def bridge(account):
    address = account.address
    nonce = eth_w3.eth.get_transaction_count(address)

    swap_txn = bridger_contract.functions.depositTransaction(address,
                                                               value,
                                                               100000,
                                                               False,
                                                               b''
    ).build_transaction({
        'from':address,
        'value': value,
        'nonce': nonce
    })

    swap_txn.update({'maxFeePerGas': eth_w3.eth.fee_history(eth_w3.eth.get_block_number(), 'latest')['baseFeePerGas'][-1] + eth_w3.eth.max_priority_fee})
    swap_txn.update({'maxPriorityFeePerGas': eth_w3.eth.max_priority_fee})

    gasLimit = eth_w3.eth.estimate_gas(swap_txn)
    swap_txn.update({'gas': gasLimit})

    signed_swap_txn = eth_w3.eth.account.sign_transaction(swap_txn, account.key)
    swap_txn_hash = eth_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
    return swap_txn_hash


def main():
    logger.info("TG channel: https://t.me/cryptomicrob")
    logger.add("./logs/bridges/bridges_ {time} .log")
    with open('private_keys.txt', 'r') as keys_file:
        accounts = [Account.from_key(line.replace("\n", "")) for line in keys_file.readlines()]
    for account in accounts:
        logger.info(f"Started work with wallet: {account.address}")
        try:
            txn = bridge(account)
            logger.success(f"Txn hash: https://etherscan.io/tx/{txn.hex()}")
        except:
            logger.exception("Error")
        logger.info(f"Ended work with wallet: {account.address}")
        time.sleep(random.randint(10, 20))

main()
