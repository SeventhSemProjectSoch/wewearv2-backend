document.addEventListener("DOMContentLoaded", function() {
    const inputs = document.querySelectorAll("input");
    if (inputs.length <= 0) return;
    inputs.forEach((input) => {
        if (input) {
            let dataList = input.parentElement.querySelector('datalist');
            if (!dataList) {
                dataList = document.createElement("datalist");
                dataList.id = `${input.getAttribute("list")}`;
                input.after(dataList);
            }
            let choices = input.getAttribute("autocomplete");
            if (choices) {
                choices.split(" ").forEach(function(choice) {
                    const option = document.createElement("option");
                    option.value = choice;
                    dataList.appendChild(option);
                });
            }
        }
    })
});