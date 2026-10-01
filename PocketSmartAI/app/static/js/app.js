async function api(url, options = {}) {

    const response = await fetch(
        url,
        {
            credentials: "same-origin",
            ...options
        }
    );

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {

        throw new Error(
            data.detail ||
            "Something went wrong."
        );
    }

    return data;
}


function formDataToJSON(form) {

    return Object.fromEntries(
        new FormData(form).entries()
    );
}


function money(value) {

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 0
        }
    ).format(
        Number(value || 0)
    );
}


function escapeHTML(value) {

    return String(
        value ?? ""
    ).replace(
        /[&<>'"]/g,
        function (character) {

            const entities = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                "'": "&#39;",
                '"': "&quot;"
            };

            return entities[character];
        }
    );
}


function escapeAttribute(value) {

    return escapeHTML(value);
}


function renderResult(data) {

    const result = data.result;

    const container =
        document.getElementById("result");

    if (!container) {
        return;
    }


    container.innerHTML = `

        <div class="result-head">

            <div>

                <p class="eyebrow">
                    AI RECOMMENDATION
                </p>

                <h2>
                    ${escapeHTML(result.title)}
                </h2>

                <p>
                    ${escapeHTML(result.summary)}
                </p>

            </div>


            <div class="budget-chip">

                ${money(result.total_estimated)}
                estimated

            </div>

        </div>


        <div class="stats">

            <div>
                <span>Budget</span>
                <b>${money(result.budget)}</b>
            </div>

            <div>
                <span>Estimated</span>
                <b>${money(result.total_estimated)}</b>
            </div>

            <div>
                <span>Remaining</span>
                <b>${money(result.savings)}</b>
            </div>

        </div>


        <div class="allocation">

            ${
                (result.allocations || [])
                    .map(
                        allocation => `

                            <div class="alloc">

                                <div>

                                    <span>
                                        ${escapeHTML(
                                            allocation.category
                                        )}
                                    </span>

                                    <b>
                                        ${money(
                                            allocation.amount
                                        )}
                                    </b>

                                </div>


                                <div class="bar">

                                    <i
                                        style="
                                            width:
                                            ${Math.min(
                                                100,
                                                Number(
                                                    allocation.percentage
                                                ) || 0
                                            )}%
                                        "
                                    ></i>

                                </div>

                            </div>
                        `
                    )
                    .join("")
            }

        </div>


        <div class="rec-grid">

            ${
                (result.recommendations || [])
                    .map(
                        recommendation => `

                            <article class="rec-card">

                                <span class="tag">

                                    ${escapeHTML(
                                        recommendation.platform
                                    )}

                                </span>


                                <h3>

                                    ${escapeHTML(
                                        recommendation.name
                                    )}

                                </h3>


                                <p class="price">

                                    ${money(
                                        recommendation.estimated_price
                                    )}

                                </p>


                                <p>

                                    ${escapeHTML(
                                        recommendation.reason
                                    )}

                                </p>


                                <a
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    href="${escapeAttribute(
                                        recommendation.link
                                    )}"
                                >
                                    View platform →
                                </a>

                            </article>

                        `
                    )
                    .join("")
            }

        </div>


        <div class="tips">

            <h3>
                Smart Tips
            </h3>


            <ul>

                ${
                    (result.tips || [])
                        .map(
                            tip => `
                                <li>
                                    ${escapeHTML(tip)}
                                </li>
                            `
                        )
                        .join("")
                }

            </ul>


            <small>

                ${escapeHTML(
                    result.disclaimer || ""
                )}

            </small>

        </div>
    `;


    container.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


async function logout() {

    try {

        await api(
            "/api/auth/logout",
            {
                method: "POST"
            }
        );

        window.location.href =
            "/login";

    } catch (error) {

        alert(error.message);
    }
}


async function plannerSubmit(
    form,
    url
) {

    const button =
        form.querySelector("button");

    const originalText =
        button.textContent;


    button.disabled = true;

    button.textContent =
        "Generating...";


    try {

        const multipart =
            form.enctype ===
            "multipart/form-data";


        const body = multipart
            ? new FormData(form)
            : JSON.stringify(
                formDataToJSON(form)
            );


        const headers = multipart
            ? {}
            : {
                "Content-Type":
                    "application/json"
            };


        const result =
            await api(
                url,
                {
                    method: "POST",
                    headers,
                    body
                }
            );


        renderResult(result);

    } catch (error) {

        alert(
            error.message
        );

    } finally {

        button.disabled = false;

        button.textContent =
            originalText;
    }
}


function setupAuthentication() {

    const loginForm =
        document.getElementById(
            "loginForm"
        );


    if (loginForm) {

        loginForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();

                try {

                    await api(
                        "/api/auth/login",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify(
                                formDataToJSON(
                                    loginForm
                                )
                            )
                        }
                    );

                    window.location.href =
                        "/dashboard";

                } catch (error) {

                    document.getElementById(
                        "formError"
                    ).textContent =
                        error.message;
                }
            }
        );
    }


    const registerForm =
        document.getElementById(
            "registerForm"
        );


    if (registerForm) {

        registerForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();

                try {

                    await api(
                        "/api/auth/register",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify(
                                formDataToJSON(
                                    registerForm
                                )
                            )
                        }
                    );

                    window.location.href =
                        "/dashboard";

                } catch (error) {

                    document.getElementById(
                        "formError"
                    ).textContent =
                        error.message;
                }
            }
        );
    }
}


function setupPlanners() {

    const homeForm =
        document.getElementById(
            "homeForm"
        );

    if (homeForm) {

        homeForm.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();

                plannerSubmit(
                    homeForm,
                    "/api/planners/home"
                );
            }
        );
    }


    const partyForm =
        document.getElementById(
            "partyForm"
        );

    if (partyForm) {

        partyForm.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();

                plannerSubmit(
                    partyForm,
                    "/api/planners/party"
                );
            }
        );
    }


    const jewelryForm =
        document.getElementById(
            "jewelryForm"
        );

    if (jewelryForm) {

        jewelryForm.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();

                plannerSubmit(
                    jewelryForm,
                    "/api/planners/jewelry"
                );
            }
        );
    }
}


async function loadHistory() {

    const container =
        document.getElementById(
            "historyList"
        );

    if (!container) {
        return;
    }


    try {

        const rows =
            await api(
                "/api/history"
            );


        if (!rows.length) {

            container.innerHTML = `

                <div class="panel">

                    <p>
                        No plans yet.
                        Create your first recommendation.
                    </p>

                </div>

            `;

            return;
        }


        container.innerHTML =
            rows.map(
                row => `

                    <div class="history-item">

                        <div>

                            <span class="tag">

                                ${escapeHTML(
                                    row.planner_type
                                )}

                            </span>


                            <h3>
                                Plan #${row.id}
                            </h3>


                            <p class="muted">

                                ${
                                    row.created_at
                                        ? new Date(
                                            row.created_at
                                        ).toLocaleString()
                                        : ""
                                }

                            </p>

                        </div>


                        <button
                            class="btn secondary"
                            onclick="viewHistory(${row.id})"
                        >
                            View
                        </button>


                        <button
                            class="danger"
                            onclick="deleteHistory(${row.id})"
                        >
                            Delete
                        </button>

                    </div>

                `
            )
            .join("");

    } catch (error) {

        container.innerHTML = `

            <p class="error">

                ${escapeHTML(
                    error.message
                )}

            </p>

        `;
    }
}


async function viewHistory(id) {

    try {

        const data =
            await api(
                `/api/history/${id}`
            );


        const result =
            data.result;


        alert(
            `${result.title}

${result.summary}

Estimated:
${money(result.total_estimated)}

Remaining:
${money(result.savings)}`
        );

    } catch (error) {

        alert(
            error.message
        );
    }
}


async function deleteHistory(id) {

    const confirmed =
        window.confirm(
            "Delete this plan?"
        );


    if (!confirmed) {
        return;
    }


    try {

        await api(
            `/api/history/${id}`,
            {
                method: "DELETE"
            }
        );

        await loadHistory();

    } catch (error) {

        alert(
            error.message
        );
    }
}


document.addEventListener(
    "DOMContentLoaded",
    function () {

        setupAuthentication();

        setupPlanners();

        loadHistory();
    }
);