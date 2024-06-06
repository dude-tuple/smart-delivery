var SmartDelivery = artifacts.require("../contracts/SmartDelivery.sol");

module.exports = async function (deployer, network, accounts) {
    const admin = accounts[0];
    deployer.deploy(SmartDelivery, admin)
};
