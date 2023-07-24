from web3 import Web3, HTTPProvider
from requests import Session
import json, random, time
from web3.auto import w3
from loguru import logger


sess = Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                     'Accept': '*/*'})

class MyHTTPProvider(HTTPProvider):
    def __init__(self, endpoint_uri, session=None, request_kwargs=None):
        super().__init__(endpoint_uri, session, request_kwargs)
        self.session = session

    def set_proxy(self, proxy):
        self.session.proxies.update({'http': proxy, 'https': proxy})

    def make_request(self, method, params):
        self.logger.debug("Making request HTTP. URI: %s, Method: %s",
                          self.endpoint_uri, method)
        request_data = self.encode_rpc_request(method, params)

        response = self.session.post(
            self.endpoint_uri,
            headers=self.get_request_headers(),
            data=request_data,
        )
        response.raise_for_status()

        return self.decode_rpc_response(response.content)


def get_proxies():
    with open("proxies.txt", 'r') as f:
        return [line.strip() for line in f]

web3 = Web3(MyHTTPProvider('https://rpc.zora.energy', session=sess))
provider = web3.provider  # Save a reference to the provider for easy access

contract_address_zora = "0x6d2C45390B2A0c24d278825c5900A1B1580f9722"
contract_abi_zora = json.load(open('./abis/zora.json'))

with open('private_keys.txt', 'r') as file:
    private_keys = [line.strip() for line in file]

zora_contract = web3.eth.contract(contract_address_zora, abi=contract_abi_zora)
zora_mint_address = w3.to_checksum_address('0x169d9147dfc9409afa4e558df2c9abeebc020182')


def mint(account):
    bytes_data = '0x000000000000000000000000' + account.address[2:]
    try:
        txn = zora_contract.functions.mint(zora_mint_address,
                                           1,
                                           1,
                                           bytes_data).build_transaction({
                                               'from': account.address,
                                               'value': web3.to_wei(0.001777, 'ether'),
                                               'nonce': web3.eth.get_transaction_count(account.address)
                                           })
        txn.update({
                'maxFeePerGas': web3.eth.fee_history(web3.eth.get_block_number(), 'latest')['baseFeePerGas'][-1] + web3.eth.max_priority_fee,
                'maxPriorityFeePerGas': web3.eth.max_priority_fee
            })
        gasLimit = web3.eth.estimate_gas(txn)
        txn.update({'gas': gasLimit})
        signed_txn = account.sign_transaction(txn)
        txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        b = web3.eth.wait_for_transaction_receipt(txn_hash)
        return b
    except Exception as e:
        print(f"Error: {e}")


def main():
    logger.info("TG channel: https://t.me/cryptomicrob")
    logger.add("./logs/mints/mints_ {time} .log")
    proxies = get_proxies()
    for private_key, proxy in zip(private_keys, proxies):
        account = web3.eth.account.from_key(private_key)
        logger.info(f"Started work with wallet: {account.address}")
        provider.set_proxy(proxy)  # Set the new proxy
        try:
            logger.success(mint(account))
        except:
            pass
        logger.info(f"Ended work with wallet: {account.address}")
        time.sleep(random.randint(10, 20))

main()