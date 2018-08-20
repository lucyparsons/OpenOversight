// Set dropdown selections to what form passed in
document.getElementById("race").value = "{{ race }}";
document.getElementById("gender").value = "{{ gender }}";
document.getElementById("rank").value = "{{ rank }}";
document.getElementById("min_age").value = "{{ min_age }}";
document.getElementById("max_age").value = "{{ max_age }}";

{% if officers.next_num %}
   var base_next_url = "/department/" + {{ department.id }} + "?page=" + {{ officers.next_num }}  + "&from_search=" + "{{ from_search}}";
{% endif %}
{% if officers.prev_num %}
   var base_prev_url = "/department/" + {{ department.id }} + "?page=" + {{ officers.prev_num }}  + "&from_search=" + "{{ from_search}}";
{% endif %}
var race_select = document.getElementById("race");
var race = race_select.options[race_select.selectedIndex].value;
var gender_select = document.getElementById("gender");
var gender = gender_select.options[gender_select.selectedIndex].value;
var rank_select = document.getElementById("rank");
var rank = rank_select.options[rank_select.selectedIndex].value;
var min_age_select = document.getElementById("min_age");
var min_age = min_age_select.options[min_age_select.selectedIndex].value;
var max_age_select = document.getElementById("max_age");
var max_age = max_age_select.options[max_age_select.selectedIndex].value;

{% if officers.next_num %}
   var next_url = base_next_url + "&race=" + race + "&gender=" + gender + "&rank=" + rank + "&min_age=" + min_age + "&max_age=" + max_age;
{% endif %}
{% if officers.prev_num %}
   var prev_url = base_prev_url + "&race=" + race + "&gender=" + gender + "&rank=" + rank + "&min_age=" + min_age + "&max_age=" + max_age;
{% endif %}

function changeURLs() {
   {% if officers.next_num %}
         next_url = base_next_url + "&race=" + race + "&gender=" + gender + "&rank=" + rank + "&min_age=" + min_age + "&max_age=" + max_age;
         document.getElementById("next_url_btn").href=next_url;
   {% endif %}
   {% if officers.prev_num %}
         prev_url = base_prev_url + "&race=" + race + "&gender=" + gender + "&rank=" + rank + "&min_age=" + min_age + "&max_age=" + max_age;
         document.getElementById("prev_url_btn").href=prev_url;
   {% endif %}
}


race_select.addEventListener('change', function(){
                                 race = this.value;
                                 changeURLs();
                              });
gender_select.addEventListener('change', function(){
                                 gender = this.value;
                                 changeURLs();
                                 });
rank_select.addEventListener('change', function(){
                                 rank = this.value;
                                 changeURLs();
                              });
min_age_select.addEventListener('change', function(){
                                 min_age = this.value;
                                 changeURLs();
                                 });
max_age_select.addEventListener('change', function(){
                                 max_age = this.value;
                                 changeURLs();
                                 });
{% if officers.next_num %}
   document.getElementById("next_url_btn").href=next_url;
{% endif %}
{% if officers.prev_num %}
   document.getElementById("prev_url_btn").href=prev_url;
{% endif %}

