document.addEventListener('DOMContentLoaded', () => {


// =========================
// AUTO CLOSE ALERTS
// =========================

document.querySelectorAll('.alert').forEach((alert) => {

    setTimeout(() => {

        bootstrap.Alert
            .getOrCreateInstance(alert)
            .close();

    }, 4500);

});

// =========================
// DASHBOARD CHART
// =========================

const chart = document.getElementById('statusChart');

if (chart) {

    const data = JSON.parse(
        chart.dataset.status || '[]'
    );

    const ctx = chart.getContext('2d');

    const width =
        chart.width = chart.clientWidth;

    const height =
        chart.height = 180;

    const max = Math.max(
        ...data.map((item) => item.count),
        1
    );

    const barWidth =
        width / Math.max(data.length, 1) - 14;

    ctx.clearRect(0, 0, width, height);

    data.forEach((item, index) => {

        const barHeight =
            (item.count / max) * 120;

        const x =
            index * (barWidth + 14) + 8;

        const y =
            height - barHeight - 34;

        ctx.fillStyle =
            index % 2
            ? '#f59e0b'
            : '#0f766e';

        ctx.fillRect(
            x,
            y,
            barWidth,
            barHeight
        );

        ctx.fillStyle = '#101828';

        ctx.font = '12px system-ui';

        ctx.fillText(
            item.label,
            x,
            height - 12
        );

    });

}

// =========================
// RAZORPAY PAYMENT
// =========================

const btn =
    document.getElementById(
        "rzp-button1"
    );

if (btn) {

    btn.addEventListener(
        "click",
        function (e) {

            e.preventDefault();

            const paymentMethod =
                document.querySelector(
                    'input[name="payment_method"]:checked'
                ).value;

            // CASH ON DELIVERY
            if (paymentMethod === "cod") {

                document.getElementById(
                    "checkout-form"
                ).submit();

                return;
            }

            // ONLINE PAYMENT
            if (paymentMethod === "gateway") {

                const options = {

                    key:
                        razorpayKeyId,

                    amount:
                        razorpayAmount,

                    currency:
                        "INR",

                    name:
                        "ShopKart",

                    description:
                        "Order Payment",

                    order_id:
                        razorpayOrderId,

                    handler: function (response){

                        console.log(
                            "PAYMENT SUCCESS"
                        );

                        console.log(
                            response
                        );

                        document.getElementById(
                            'razorpay_payment_id'
                        ).value =
                            response.razorpay_payment_id;

                        document.getElementById(
                            'razorpay_order_id'
                        ).value =
                            response.razorpay_order_id;

                        document.getElementById(
                            'razorpay_signature'
                        ).value =
                            response.razorpay_signature;

                        document.getElementById(
                            'checkout-form'
                        ).submit();
                    },

                    modal: {

                        ondismiss: function(){

                            console.log(
                                "Payment popup closed"
                            );

                        }
                    },

                    theme: {
                        color: "#3399cc"
                    }
                };

                const rzp =
                    new Razorpay(options);

                // PAYMENT FAILED
                rzp.on(
                    'payment.failed',
                    function (response){

                        console.log(
                            response.error
                        );

                        alert(
                            "Payment Failed"
                        );

                    }
                );

                rzp.open();
            }

        }
    );

}



const toggleBtn =
    document.getElementById(
        "theme-toggle"
    );

// LOAD SAVED THEME
if(localStorage.getItem("theme") === "dark") {

    document.body.classList.add(
        "dark-mode"
    );

    if(toggleBtn){

        toggleBtn.innerHTML = "☀️";
    }
}

// TOGGLE THEME
if(toggleBtn){

    toggleBtn.addEventListener(
        "click",
        function () {

            document.body.classList.toggle(
                "dark-mode"
            );

            // SAVE THEME
            if(document.body.classList.contains("dark-mode")) {

                localStorage.setItem(
                    "theme",
                    "dark"
                );

                toggleBtn.innerHTML = "☀️";

            } else {

                localStorage.setItem(
                    "theme",
                    "light"
                );

                toggleBtn.innerHTML = "🌙";
            }
        }
    );
}


});
