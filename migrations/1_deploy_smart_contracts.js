require('dotenv').config({ path: '../.env'});

var SmartDelivery = artifacts.require("../contracts/SmartDelivery.sol");
const expirationMinutes = process.env.EXPIRATION_MINUTES || 5;

module.exports = async function (deployer, network, accounts) {
    const admin = accounts[0];
    deployer.deploy(SmartDelivery, admin, expirationMinutes);
};
