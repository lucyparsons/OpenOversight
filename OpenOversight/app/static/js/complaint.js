$(document).ready(function() {

    // var navListItems = $('ul.setup-panel li a'),
    //     allWells = $('.setup-content');
    //
    // allWells.hide();
    //
    // navListItems.click(function(e)
    // {
    //     e.preventDefault();
    //     var $target = $($(this).attr('href')),
    //         $item = $(this).closest('li');
    //
    //     if (!$item.hasClass('disabled')) {
    //         navListItems.closest('li').removeClass('active');
    //         $item.addClass('active');
    //         allWells.hide();
    //         $target.show();
    //     }
    // });
    //
    // $('ul.setup-panel li.active a').trigger('click');
    //
    // $('#activate-step-2').on('click', function(e) {
    //     $('ul.setup-panel li:eq(1)').removeClass('disabled');
    //     $('ul.setup-panel li a[href="#step-2"]').trigger('click');
    //     $(this).remove();
    // })
    // $('#activate-step-3').on('click', function(e) {
    //     $('ul.setup-panel li:eq(2)').removeClass('disabled');
    //     $('ul.setup-panel li a[href="#step-3"]').trigger('click');
    //     $(this).remove();
    // })
    // $('#activate-step-4').on('click', function(e) {
    //     $('ul.setup-panel li:eq(3)').removeClass('disabled');
    //     $('ul.setup-panel li a[href="#step-4"]').trigger('click');
    //     $(this).remove();
    // })

    $('#step-1').on('click', function(e) {
      e.preventDefault()
      document.querySelector('#step-1').scrollIntoView({
        behavior: 'smooth'
      });
    })

    // Generate loading notification
    $("#user-notification").on("click", function(){
       $("#loader").show();
    });

    // Show/hide ranks
    $("#show_img").on("click", function(){
       $("#hidden_img").show();
       $("#show_img_div").hide();
    });

    $("#hide_img").click(function(){
       $("#hidden_img").hide();
       $("#show_img_div").show();
    });
});
