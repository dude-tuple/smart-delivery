const SmartDelivery = artifacts.require("SmartDelivery");

module.exports = function (deployer, network, accounts) {
    const receiver = accounts[1];
    const minTemp = 2;
    const maxTemp = 8;
    const deliveryId = "delivery123";
    const deposit = web3.utils.toWei('1', 'ether');

    deployer.deploy(SmartDelivery, receiver, minTemp, maxTemp, deliveryId, { value: deposit, from: accounts[0] });
};
