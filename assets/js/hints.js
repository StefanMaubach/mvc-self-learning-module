// Initial setup for hint variables and show_all_hints flags
var show_all_hints = 0;
var hint_1 = 0;
var hint_2 = 0;
var hint_3 = 0;
var hint_4 = 0;
var hint_5 = 0;
var hint_6 = 0;
var hint_7 = 0;
var hint_8 = 0;
var hint_9 = 0;
var hint_10 = 0;
var hint_11 = 0;
var hint_12 = 0;
var hint_13 = 0;
var hint_14 = 0;
var hint_15 = 0;
var hint_16 = 0;
var hint_17 = 0;
var hint_18 = 0;
var hint_19 = 0;
var hint_20 = 0;

// Function to update the hint variables
function var_change_hint(hint_num, hint_now) {
  if (hint_num == 1) hint_1 = hint_now;
  if (hint_num == 2) hint_2 = hint_now;
  if (hint_num == 3) hint_3 = hint_now;
  if (hint_num == 4) hint_4 = hint_now;
  if (hint_num == 5) hint_5 = hint_now;
  if (hint_num == 6) hint_6 = hint_now;
  if (hint_num == 7) hint_7 = hint_now;
  if (hint_num == 8) hint_8 = hint_now;
  if (hint_num == 9) hint_9 = hint_now;
  if (hint_num == 10) hint_10 = hint_now;
  if (hint_num == 11) hint_11 = hint_now;
  if (hint_num == 12) hint_12 = hint_now;
  if (hint_num == 13) hint_13 = hint_now;
  if (hint_num == 14) hint_14 = hint_now;
  if (hint_num == 15) hint_15 = hint_now;
  if (hint_num == 16) hint_16 = hint_now;
  if (hint_num == 17) hint_17 = hint_now;
  if (hint_num == 18) hint_18 = hint_now;
  if (hint_num == 19) hint_19 = hint_now;
  if (hint_num == 20) hint_20 = hint_now;
}

// Function to display or hide a collection of elements
function disp(collection, num) {
  for (let i = 0; i < collection.length; i++) {
    collection[i].style.display = num ? "inline-block" : "none";
  }
}

// Function to handle the hide/show behavior for the main button
function HideShow(in_but, in_focus) {
  let elem = document.getElementById(in_but);
  const collection_but = document.getElementsByClassName(in_focus);
  const collection_child = document.getElementsByClassName(in_focus + "_child");

  if (in_focus == "unsee_hint") {
    if (show_all_hints == 0) {
      elem.innerHTML = "Hide Hints";
      show_all_hints = 1;
      disp(collection_but, 1);
    } else {
      elem.innerHTML = "Show Hints";
      show_all_hints = 0;
      disp(collection_but, 0);
      disp(collection_child, 0);
      for (let i = 1; i <= 20; i++) {
        if (eval("hint_" + i) == 1) {
          hint_show(i);
        }
      }
    }
  }
}

// Function to show or hide specific hints and reveal the next hint button
function hint_show(hint_num) {
  var step_box = document.getElementById(hint_num);
  var hint_box = document.getElementById("hint_" + hint_num);
  var hint_but = document.getElementById("but_" + hint_num + "_1");
  var hint_now = eval("hint_" + hint_num);

  if (hint_now == 0) {
    hint_box.style.display = "block";
    step_box.style.display = "flex";
    hint_now = 1;
  } else {
    hint_box.style.display = "none";
    hint_now = 0;
  }
  var_change_hint(hint_num, hint_now);

  // Show the next hint button
  var next_hint_num = hint_num + 1;
  if (next_hint_num <= 20) {
    var next_hint_but = document.getElementById("but_" + next_hint_num + "_1");
    if (next_hint_but) {
      next_hint_but.style.display = "inline-block";
    }
  }
}

// Initially, only show the first hint button
window.onload = function () {
  for (let i = 2; i <= 20; i++) {
    var hint_but = document.getElementById("but_" + i + "_1");
    if (hint_but) {
      hint_but.style.display = "none";
    }
  }
};
