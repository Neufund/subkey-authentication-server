from ethereum.utils import decode_hex, encode_hex, sha3


def pub_to_addr(pub_key):
    public_key_binary = decode_hex(pub_key)[1:]
    pub_key_hash = sha3(public_key_binary)
    address_binary = pub_key_hash[12:]
    address_bytes = encode_hex(address_binary)
    address = address_bytes.decode("utf-8")
    return "0x" + address


def wallet_to_addr(wallet):
    return pub_to_addr(wallet.public_key.get_key())
