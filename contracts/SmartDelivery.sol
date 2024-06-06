// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract SmartDelivery {
    struct Requirements {
        uint256 minTemp;
        uint256 maxTemp;
        uint256 minHumidity;
        uint256 maxHumidity;
    }

    struct Payment {
        uint256 deliveryPrice;
        uint256 productPrice;
        bool paymentReleased;
    }

    struct Parties {
        address provider;
        address deliverer;
        address client;
    }

    struct Delivery {
        Parties parties;
        Requirements requirements;
        Payment payment;
        uint256 endTime;
        bool active;
        string deliveryId;
    }

    struct DeliveryDetails {
        address provider;
        address deliverer;
        address client;
        uint256 minTemp;
        uint256 maxTemp;
        uint256 minHumidity;
        uint256 maxHumidity;
        uint256 deliveryPrice;
        uint256 productPrice;
        uint256 endTime;
        bool paymentReleased;
        bool active;
        string deliveryId;
    }

    address public admin;
    mapping(string => Delivery) public deliveries;
    string[] public deliveryIds;  // Auxiliary array to track delivery IDs

    event DeliveryStarted(address indexed provider, address indexed deliverer, address indexed client, uint256 deliveryPrice, uint256 productPrice, string deliveryId);
    event DeliveryCompleted(uint256 endTime, bool success, string message, string deliveryId);
    event PaymentReleased(address indexed deliverer, uint256 amount, string deliveryId);
    event PaymentRefunded(address indexed client, uint256 amount, string deliveryId);
    event ProviderPaid(address indexed provider, uint256 amount, string deliveryId);
    event DeliveryCleared(string deliveryId);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    constructor(address _admin) {
        require(_admin != address(0), "Invalid admin address");
        admin = _admin;
    }

    function startDelivery(
        address _provider,
        address _deliverer,
        uint256 _minTemp,
        uint256 _maxTemp,
        uint256 _minHumidity,
        uint256 _maxHumidity,
        uint256 _productPrice,
        uint256 _deliveryPrice,
        string memory _deliveryId
    ) public payable {
        require(!deliveries[_deliveryId].active, "Delivery ID already in use");
        require(msg.value == _productPrice + _deliveryPrice, "Incorrect Ether sent");

        // Transfer the product price to the provider immediately
        payable(_provider).transfer(_productPrice);
        emit ProviderPaid(_provider, _productPrice, _deliveryId);

        deliveries[_deliveryId] = Delivery({
            parties: Parties({
                client: msg.sender,
                deliverer: _deliverer,
                provider: _provider
            }),
            requirements: Requirements({
                minTemp: _minTemp,
                maxTemp: _maxTemp,
                minHumidity: _minHumidity,
                maxHumidity: _maxHumidity
            }),
            payment: Payment({
                deliveryPrice: _deliveryPrice,
                productPrice: _productPrice,
                paymentReleased: false
            }),
            endTime: 0,
            active: true,
            deliveryId: _deliveryId
        });

        deliveryIds.push(_deliveryId);
        emit DeliveryStarted(msg.sender, _deliverer, _provider, _deliveryPrice, _productPrice, _deliveryId);
    }

    function completeDelivery(
        string memory _deliveryId,
        uint256 _endTime,
        uint256 _avgTemp,
        uint256 _avgHumidity
    ) public {
        Delivery storage delivery = deliveries[_deliveryId];
        require(msg.sender == delivery.parties.client, "Only the client can complete the delivery");
        require(delivery.active, "No active delivery to complete");
        require(!delivery.payment.paymentReleased, "Payment already released");

        delivery.endTime = _endTime;
        delivery.active = false;

        bool success = checkDeliveryConditions(delivery, _avgTemp, _avgHumidity);
        handlePayment(delivery, success, _deliveryId);

        emit DeliveryCompleted(delivery.endTime, success, success ? "Delivery conditions met" : "Delivery conditions not met", _deliveryId);
    }

    function checkDeliveryConditions(Delivery storage delivery, uint256 avgTemp, uint256 avgHumidity) internal view returns (bool) {
        return avgTemp >= delivery.requirements.minTemp && avgTemp <= delivery.requirements.maxTemp &&
               avgHumidity >= delivery.requirements.minHumidity && avgHumidity <= delivery.requirements.maxHumidity;
    }

    function handlePayment(Delivery storage delivery, bool success, string memory deliveryId) internal {
        if (success) {
            releasePayment(delivery, deliveryId);
        } else {
            refundPayment(delivery, deliveryId);
        }
    }

    function releasePayment(Delivery storage delivery, string memory deliveryId) internal {
        require(address(this).balance >= delivery.payment.deliveryPrice, "Insufficient balance in contract");

        payable(delivery.parties.deliverer).transfer(delivery.payment.deliveryPrice);
        delivery.payment.paymentReleased = true;
        emit PaymentReleased(delivery.parties.deliverer, delivery.payment.deliveryPrice, deliveryId);
    }

    function refundPayment(Delivery storage delivery, string memory deliveryId) internal {
        require(address(this).balance >= delivery.payment.deliveryPrice, "Insufficient balance in contract");

        payable(delivery.parties.client).transfer(delivery.payment.deliveryPrice);
        delivery.payment.paymentReleased = false;
        emit PaymentRefunded(delivery.parties.client, delivery.payment.deliveryPrice, deliveryId);
    }

    function clearOldDeliveries() public onlyAdmin {
        uint256 currentTime = block.timestamp;
        uint256 fiveMinutes = 5 * 60;
        uint256 i = 0;

        while (i < deliveryIds.length) {
            string memory deliveryId = deliveryIds[i];
            Delivery storage delivery = deliveries[deliveryId];

            if (!delivery.active && currentTime > delivery.endTime + fiveMinutes) {
                delete deliveries[deliveryId];  // Delete the delivery data from mapping
                deliveryIds[i] = deliveryIds[deliveryIds.length - 1];
                deliveryIds.pop();
                emit DeliveryCleared(deliveryId);
            } else {
                i++;
            }
        }
    }

    function getDelivery(string memory _deliveryId) public view returns (DeliveryDetails memory) {
        Delivery storage delivery = deliveries[_deliveryId];
        return DeliveryDetails({
            provider: delivery.parties.provider,
            deliverer: delivery.parties.deliverer,
            client: delivery.parties.client,
            minTemp: delivery.requirements.minTemp,
            maxTemp: delivery.requirements.maxTemp,
            minHumidity: delivery.requirements.minHumidity,
            maxHumidity: delivery.requirements.maxHumidity,
            deliveryPrice: delivery.payment.deliveryPrice,
            productPrice: delivery.payment.productPrice,
            endTime: delivery.endTime,
            paymentReleased: delivery.payment.paymentReleased,
            active: delivery.active,
            deliveryId: delivery.deliveryId
        });
    }
}
