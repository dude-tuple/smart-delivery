pragma solidity ^0.8.13;

contract SmartDelivery {
    struct Delivery {
        address provider;
        address customer;
        uint256 requiredMinTemp;
        uint256 requiredMaxTemp;
        uint256 requiredMinHumidity;
        uint256 requiredMaxHumidity;
        uint256 deposit;
        uint256 endTime;
        bool paymentReleased;
        bool active;
        string deliveryId;
    }

    mapping(string => Delivery) public deliveries;

    event DeliveryStarted(address indexed provider, address indexed customer, uint256 deposit, string deliveryId);
    event DeliveryCompleted(uint256 endTime, bool success, string message, string deliveryId);
    event PaymentReleased(address indexed customer, uint256 amount, string deliveryId);
    event PaymentRefunded(address indexed provider, uint256 amount, string deliveryId);

    function startDelivery(
        address _customer,
        uint256 _requiredMinTemp,
        uint256 _requiredMaxTemp,
        uint256 _requiredMinHumidity,
        uint256 _requiredMaxHumidity,
        string memory _deliveryId
    ) public payable {
        require(deliveries[_deliveryId].active == false, "Delivery ID already in use");

        deliveries[_deliveryId] = Delivery({
            provider: msg.sender,
            customer: _customer,
            requiredMinTemp: _requiredMinTemp,
            requiredMaxTemp: _requiredMaxTemp,
            requiredMinHumidity: _requiredMinHumidity,
            requiredMaxHumidity: _requiredMaxHumidity,
            deposit: msg.value,
            endTime: 0,
            paymentReleased: false,
            active: true,
            deliveryId: _deliveryId
        });

        emit DeliveryStarted(msg.sender, _customer, msg.value, _deliveryId);
    }

    function completeDelivery(
        string memory _deliveryId,
        uint256 _endTime,
        uint256 _avgTemp,
        uint256 _avgHumidity
    ) public {
        Delivery storage delivery = deliveries[_deliveryId];
        require(msg.sender == delivery.customer, "Only the customer can complete the delivery");
        require(delivery.active, "No active delivery to complete");
        require(!delivery.paymentReleased, "Payment already released");

        delivery.endTime = _endTime;
        delivery.active = false;
        bool success = _avgTemp >= delivery.requiredMinTemp && _avgTemp <= delivery.requiredMaxTemp &&
                       _avgHumidity >= delivery.requiredMinHumidity && _avgHumidity <= delivery.requiredMaxHumidity;

        if (success) {
            payable(delivery.customer).transfer(delivery.deposit);
            delivery.paymentReleased = true;
            emit PaymentReleased(delivery.customer, delivery.deposit, _deliveryId);
        } else {
            payable(delivery.provider).transfer(delivery.deposit);
            emit PaymentRefunded(delivery.provider, delivery.deposit, _deliveryId);
        }

        emit DeliveryCompleted(delivery.endTime, success, success ? "Delivery conditions met" : "Delivery conditions not met", _deliveryId);
    }

    function getDelivery(string memory _deliveryId) public view returns (
        address provider,
        address customer,
        uint256 requiredMinTemp,
        uint256 requiredMaxTemp,
        uint256 requiredMinHumidity,
        uint256 requiredMaxHumidity,
        uint256 deposit,
        uint256 endTime,
        bool paymentReleased,
        bool active,
        string memory deliveryId
    ) {
        Delivery storage delivery = deliveries[_deliveryId];
        return (
            delivery.provider,
            delivery.customer,
            delivery.requiredMinTemp,
            delivery.requiredMaxTemp,
            delivery.requiredMinHumidity,
            delivery.requiredMaxHumidity,
            delivery.deposit,
            delivery.endTime,
            delivery.paymentReleased,
            delivery.active,
            delivery.deliveryId
        );
    }
}
