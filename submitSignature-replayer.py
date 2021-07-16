#!/usr/bin/env python
# coding: utf-8

import sys

import toml
from json import load, loads
from os import listdir
from os.path import isfile, join
import argparse

from web3 import Web3, HTTPProvider
from eth_account import Account
from urllib import request
from urllib.error import URLError, HTTPError

import logging

logging.basicConfig(format='%(levelname)s:%(message)s', 
                    level=logging.INFO)

DEFAULT_CONFIG_FILE = 'config.toml'
GAS_PRICE_SPEED = 'fast'
GAS_PRICE_ORACLE_URL = 'http://ethgas.watch/api/gas'

parser = argparse.ArgumentParser(description='submitSignature relayer')
parser.add_argument('-c', dest='config', default=DEFAULT_CONFIG_FILE, metavar='<toml-file>')
parser.add_argument('transaction')
args = parser.parse_args()

config_file = args.config
cloned_tx = args.transaction
logging.info(f'Tx to be cloned: {cloned_tx}')
logging.info(f'Config file: {config_file}')

with open(config_file) as toml_file:
    config = toml.load(toml_file)
logging.info(f'Config file read')

keys_dir = config['keystore']
onlyfiles = [f for f in listdir(keys_dir) if isfile(join(keys_dir, f))]
if len(onlyfiles) > 0:
    key_file = join(keys_dir, onlyfiles[0])
else:
    raise OSError('Cannot find the key files')
logging.info(f'Keyfile found in "{key_file}"')

pass_file = config['foreign']['password']
with open(pass_file) as txt_file:
    key_pass = txt_file.readlines()[0].strip()
logging.info(f'Password read')

web3_provider = config['foreign']['rpc_host']
logging.info(f'Using RPC URL "{web3_provider}"')

gas_limit = config['transactions']['withdraw_confirm']['gas']
logging.info(f'Using gas limit {gas_limit}')

with open(key_file) as json_file:
    encrypted = load(json_file)
logging.info(f'Keyfile read for 0x{encrypted["address"]}')

try:
    pk = Account.decrypt(encrypted, key_pass)
except:
    logging.error('Cannot decrypt the key')
    raise sys.exc_info()[1]

acc = Account.privateKeyToAccount(pk)
logging.info(f'Keyfile decrypted successfully')

w3 = Web3(HTTPProvider(web3_provider))

try: 
    response = request.urlopen(GAS_PRICE_ORACLE_URL)
    raw_data = response.readlines()
    data_json = loads(raw_data[0])
    gas_price = Web3.toWei(data_json[GAS_PRICE_SPEED]['gwei'], 'gwei')
except URLError:
    logging.warning('Gas Price Oracle is not available')
    gas_price = Web3.toWei(21, 'gwei')
logging.info(f'Using gas price {gas_price}')

try:
    chainid = w3.eth.chain_id
except:
    logging.error(f'Transaction count cannot be received')
    raise sys.exc_info()[1]

logging.info(f'Using chain id {chainid}')

try:
    nonce = w3.eth.getTransactionCount(acc.address)
except:
    logging.error(f'Transaction count cannot be received')
    raise sys.exc_info()[1]

logging.info(f'Using nonce {nonce}')

try:
    origin_tx = w3.eth.getTransaction(cloned_tx)
except:
    logging.error(f'Base transaction cannot be found')
    raise sys.exc_info()[1]

logging.info(f'Tx found in the block {origin_tx.blockNumber}')

tx = {
    'from': acc.address,
    'chainId': chainid,
    'to': origin_tx['to'],
    'gasPrice': gas_price,
    'data': origin_tx['input'],
    'nonce': nonce,
    'value': 0
}

try:
    gas_limit = w3.eth.estimate_gas(tx)
except:
    logging.error(f'Cannot estimate gas')
    raise sys.exc_info()[1]

gas_limit = int(gas_limit * 1.25)
logging.info(f'Usign gas limit {gas_limit}')

tx['gas'] = gas_limit

raw_tx = acc.signTransaction(tx)
logging.info(f'New tx prepared and signed')

try:
    tx_hash = w3.eth.sendRawTransaction(raw_tx.rawTransaction)
except:
    logging.error(f'Transaction was not sent')
    raise sys.exc_info()[1]

logging.info(f'Transaction {Web3.toHex(tx_hash)} sent')

try:
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=1)
except:
    logging.error(f'Transaction receipt cannot be found')
    receipt = None
    raise sys.exc_info()[1]

if (receipt != None):
    if (receipt.status == 0):
        logging.error(f'Transaction failed')
    else:
        logging.info(f'Transaction successfully included in block {receipt.blockNumber}')
