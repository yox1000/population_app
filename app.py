from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

AGE_BRACKETS = [
    "0-9", "10-19", "20-29", "30-39", "40-49",
    "50-59", "60-69", "70-79", "80-89", "90-99", "100+"
]

@app.route("/", methods=["GET", "POST"])
def index():
    chart_url = None
    error = None
    males = []
    females = []

    if request.method == "POST":
        try:
            males = [float(request.form[f"male_{i}"]) for i in range(len(AGE_BRACKETS))]
            females = [float(request.form[f"female_{i}"]) for i in range(len(AGE_BRACKETS))]

            total_population = sum(males) + sum(females)
            if abs(total_population - 100) > 0.01:
                error = f"Total population percentages must add up to 100. Current total: {total_population:.2f}"
            else:
                # Convert male percentages to negative for left side bars
                males_neg = [-v for v in males]

                fig, ax = plt.subplots(figsize=(8, 6))
                y_pos = range(len(AGE_BRACKETS))

                ax.barh(y_pos, males_neg, color='blue', label='Male')
                ax.barh(y_pos, females, color='pink', label='Female')

                ax.set_yticks(y_pos)
                ax.set_yticklabels(AGE_BRACKETS)
                ax.set_xlabel('Population Percentage')
                ax.set_title('Population Pyramid')
                ax.legend()

                ax.grid(axis='x', linestyle='--', alpha=0.7)
                plt.tight_layout()

                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                chart_url = base64.b64encode(buf.getvalue()).decode('utf-8')
                plt.close()

        except Exception as e:
            error = f"Error processing form data: {e}"

    return render_template("index.html", age_brackets=AGE_BRACKETS,
                           chart_url=chart_url, error=error,
                           males=males, females=females)

if __name__ == "__main__":
    app.run(debug=True)
