function set_jobs() {
  var dept_id = $('#department').val();
  // fetch jobs for dept_id and modify #job_titles <select>
  var jobs_url = $('#add-officer-form').data('jobs-url');
  var jobs = $.ajax({
    url: jobs_url,
    data: {department_id: dept_id}
  }).done(function(jobs) {
    $('#job_title').replaceWith('<select class="form-control" id="job_title" name="job_title">');
    for (i = 0; i < jobs.length; i++) {
      $('select#job_title').append(
        $('<option></option>').attr("value", jobs[i][0]).text(jobs[i][1])
      );
    }
  });
}

$(document).ready(function() {
  set_jobs();
  $('select#department').change(set_jobs);
});
