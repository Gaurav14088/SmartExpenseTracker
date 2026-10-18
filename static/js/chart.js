
const canvas = document.getElementById("expenseChart");
const expenseElement = document.getElementById("monthly-expense");

if (canvas && expenseElement && typeof Chart !== "undefined") {
    const spent = Number(expenseElement.dataset.amount || 0);
    const budget = 10000;
    const remaining = Math.max(budget - spent, 0);

    let chartColor;

    if (spent < 5000) {
        chartColor = "#22c55e";
    } else if (spent < 8000) {
        chartColor = "#eab308";
    } else {
        chartColor = "#ef4444";
    }

    // Display values in the centre of the pie chart
    const centerText = {
        id: "centerText",
        afterDraw(chart) {
            const { ctx, chartArea } = chart;
            if (!chartArea) return;

            const x = (chartArea.left + chartArea.right) / 2;
            const y = (chartArea.top + chartArea.bottom) / 2;

            ctx.save();
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            ctx.fillStyle = "#f5f3ff";
            ctx.font = "bold 22px Arial";
            ctx.fillText(
                "₹" + spent.toLocaleString("en-IN"),
                x,
                y - 10
            );

            ctx.fillStyle = "#9691a8";
            ctx.font = "12px Arial";
            ctx.fillText("Total Spent", x, y + 15);

            ctx.restore();
        }
    };

    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: ["Spent", "Remaining Budget"],
            datasets: [{
                data: [Math.min(spent, budget), remaining],
                backgroundColor: [chartColor, "#30293a"],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            cutout: "68%",
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#f5f3ff",
                        padding: 18
                    }
                },
                tooltip: {
                    callbacks: {
                        label(context) {
                            return context.label + ": ₹" +
                                Number(context.raw).toLocaleString("en-IN");
                        }
                    }
                }
            }
        },
        plugins: [centerText]
    });
}
