function main() {
    var toggler = document.getElementsByClassName("caret");
    var i;

    for (i = 0; i < toggler.length; i++) {
        toggler[i].addEventListener("click", function() {
            this.parentElement.querySelector(".nested").classList.toggle("active");
            this.classList.toggle("caret-down");
        });
    }
}

function copyByID(elementId) {
  var copyText = document.getElementById(elementId);
  copyToClipboard(copyText.textContent);

  var tooltip = document.getElementById(elementId.concat("Tooltip"));
  tooltip.innerHTML = "Copied: " + copyText.textContent;
}

function outFunc(tooltipId) {
  var tooltip = document.getElementById(tooltipId);
  tooltip.innerHTML = "Copy to clipboard";
}

// Using function found here:
// https://github.com/30-seconds/30-seconds-of-code#copytoclipboard-
function copyToClipboard(str) {
    var el = document.createElement('textarea');
    el.value = str;
    el.setAttribute('readonly', '');
    el.style.position = 'absolute';
    el.style.left = '-9999px';
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
}