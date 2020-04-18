function autocomplete(inp, url) {
	var currentFocus;
    var inputEl;
    var textStartPos;
    var preventEnter;

    if (!inp) {
        console.log("No input to autocomplete");
        return false;
    }

    function escapeHtml(text) {
        var map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };

        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

	function onLoad() {
		var a, b, i, val = inputEl.value;
		closeAllLists();
		if (!xhr.responseText) {
			return false;
		}
		var arr = JSON.parse(xhr.responseText);
		console.log(arr);
		if (!val || !arr) {
			return false;
		}
		currentFocus = -1;

		a = document.createElement("DIV");
		a.setAttribute("id", inputEl.id + "autocomplete-list");
		a.setAttribute("class", "autocomplete-items");
		inputEl.parentNode.appendChild(a);

        var caretPos = inputEl.selectionEnd || 0;
		for (i = 0; i < arr.length; i++) {
            /*create a DIV element for each matching element:*/
            b = document.createElement("DIV");
            /*make the matching letters bold:*/
            b.innerHTML = "<strong>" + escapeHtml(arr[i].substr(0, caretPos - textStartPos)) + "</strong>";
            b.innerHTML += escapeHtml(arr[i].substr(caretPos - textStartPos));
            /*insert a input field that will hold the current array item's value:*/
            b.innerHTML += "<input type='hidden' value='" + escapeHtml(arr[i]) + "'>";
            /*execute a function when someone clicks on the item value (DIV element):*/
                    b.addEventListener("click", function(e) {
                    /*insert the value for the autocomplete text field:*/
                    inp.value = inp.value.substr(0, textStartPos) + this.getElementsByTagName("input")[0].value;
                    /*close the list of autocompleted values,
                    (or any other open lists of autocompleted values:*/
                    closeAllLists();
            });
            a.appendChild(b);
		}
        
        preventEnter = true;
	}
	
	function onInput () {
		var val = this.value;
		if (!val) {
            closeAllLists();
			return false;
		}
        inputEl = this;
		
		var pos = inputEl.selectionEnd || 0;
		var spacePos = val.indexOf(" ");
		var nextPos = spacePos;
		while(nextPos < pos && nextPos > -1) {
			spacePos = nextPos;
			nextPos = val.indexOf(" ", spacePos + 1);
		}
		if(spacePos > pos || spacePos < 0)
			spacePos = -1;
		startPos = spacePos + 1;
		term = val.substring(startPos, pos + 1);
        textStartPos = startPos;
						
		var urlargs = encodeURIComponent(term);
		
		xhr = new XMLHttpRequest();
		xhr.addEventListener("error", function() {
			console.log(xhr, "error");
			closeAllLists();
		});
		xhr.addEventListener("load", onLoad);
		xhr.open("GET", url + urlargs);
		xhr.send();
	}
	
	inp.addEventListener("input", onInput);
	
	
	/*execute a function presses a key on the keyboard:*/
	inp.addEventListener("keydown", function(e) {
			var x = document.getElementById(this.id + "autocomplete-list");
			if (x) x = x.getElementsByTagName("div");
			if (e.keyCode == 40) {
				/*If the arrow DOWN key is pressed,
				increase the currentFocus variable:*/
				currentFocus++;
				/*and and make the current item more visible:*/
				addActive(x);
			} else if (e.keyCode == 38) { //up
				/*If the arrow UP key is pressed,
				decrease the currentFocus variable:*/
				currentFocus--;
				/*and and make the current item more visible:*/
				addActive(x);
			} else if (e.keyCode == 13) {
				/*If the ENTER key is pressed, prevent the form from being submitted,*/
				if(preventEnter) {
                    e.preventDefault();
                }
				if (currentFocus > -1) {
					/*and simulate a click on the "active" item:*/
					if (x) x[currentFocus].click();
				} else {
                    var form = document.getElementById("searchform");
                    if (form) {
                        form.submit();
                    }
                }
			}
	});
	function addActive(x) {
		/*a function to classify an item as "active":*/
		if (!x) return false;
		/*start by removing the "active" class on all items:*/
		removeActive(x);
		if (currentFocus >= x.length) currentFocus = 0;
		if (currentFocus < 0) currentFocus = (x.length - 1);
		/*add class "autocomplete-active":*/
		x[currentFocus].classList.add("autocomplete-active");
        preventEnter = true;
	}
	function removeActive(x) {
		/*a function to remove the "active" class from all autocomplete items:*/
		for (var i = 0; i < x.length; i++) {
			x[i].classList.remove("autocomplete-active");
		}
	}
	function closeAllLists(elmnt) {
		/*close all autocomplete lists in the document,
		except the one passed as an argument:*/
		var x = document.getElementsByClassName("autocomplete-items");
		for (var i = 0; i < x.length; i++) {
			if (elmnt != x[i] && elmnt != inp) {
			x[i].parentNode.removeChild(x[i]);
			}
		}
        preventEnter = false;
	}
	/*execute a function when someone clicks in the document:*/
	document.addEventListener("click", function (e) {
			closeAllLists(e.target);
	});
} 
