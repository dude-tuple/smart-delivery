const HDWalletProvider = require('@truffle/hdwallet-provider');

const mnemonic = "profit join hub veteran web session retire zero slush toddler tissue cook";

module.exports = {
  networks: {
    development: {
      provider: () => new HDWalletProvider(mnemonic, 'http://127.0.0.1:7545'),
      network_id: '*',
      gas: 6721975,
      gasPrice: 20000000000
    }
  },
  compilers: {
    solc: {
      version: "0.8.13"
    }
  }
};
