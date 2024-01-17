//

async function setup () {

    const questions_url = `${server_url}/questions/`;
    let data = null;
    try {
        data = await fetch(questions_url);
        data = await data.json();
        console.log('data', data);
    } catch (error) {
        console.log('error', error);
    }
    if (data['error'] !== undefined) {
        alert('Sorry, it appears the maximum number of attempts was already performed');
        return;
    }
    const questions = data['questions'];
    questions.forEach(function (item, item_no) {
        // item_no = questions.length - item_no - 1;
        // var row = d3.select('.questionnaire')
        //             // .append('div')
        //             .insert("div",":first-child")
        //             // .insert("div",":last-child")
        //             .attr('class', 'form-row');
        // var col = row.append('div')
        //                 .attr('class', 'col-12');

        // var div = col.append('div')
        //                 .attr('class' , 'form-group');

        // // no-incentive
        // if(item['question'].toLowerCase().includes('bonus')) {
        //     return;
        // }

        const div = d3.select('.questionnaire')
                    .append('div', ":first-child")
                    .attr('class' , 'form-group');
                        
        div.append('label', ":first-child")
            .html(item['question']);

        // all questions are multiple choice question
        item['choices'].forEach( function (choice, i) {
            var html = `
            <input class="form-check-input item${item_no}-radios" 
                    type="radio" 
                    name="item${item_no}-radios" 
                    id="item${item_no}-radio${i}" 
                    value="${choice.id}" 
                    required>
                <label class="form-check-label" 
                        for="item${item_no}-radio${i}">
                        ${choice.text}
                </label>
            `;
            const item_div = div.append('div', ":first-child")
                .attr('class', 'form-check')
                .html(html);
            // if (i === (item.choices.length - 1)) {
            //     item_div.append('div')
            //             .attr('class', "invalid-feedback")
            //             .html('Please select an answer.');
            // }
        });
                        
    });

    $('button.startShopButton').attr('disabled', 'disabled');
    setTimeout(function()
    {
       $('button.startShopButton').removeAttr('disabled')
    },180000)

    // make the checkboxes valid as soon as one item is selected
    d3.selectAll('.form-check-input')
        .on('click', function (d) {
            // get item_no
            var item = d3.select(this).attr('id').split('-')[0];
            d3.selectAll(`.${item}-radios`).classed('is-invalid', false);
      });

    const button_div = d3.select('.questionnaire')
                .append('div')
                .attr('class', 'form-row')
                .html(`
        <div class="col-12">
            <button type="button" id="submit-btn" class="btn btn-lg btn-primary">Submit</button>
        </div>`);
   
    

    d3.select('#submit-btn').on('click', function () {
        // calculate task completion time
        var end = performance.now();
        var task_completion_time = end - start;

        console.log('task_completion_time:', task_completion_time);

        // get the form data
        var results = [];
        var errors = false;
        questions.forEach( function (item, item_no) {
            let answer = undefined;
            let choice_id = undefined;
            // multiple choice question
            const selected = d3.select(`input[name="item${item_no}-radios"]:checked`);
            if (selected.node() === null) {
                answer = '';
                mising_data = true;
                d3.selectAll(`.item${item_no}-radios`).classed('is-invalid', true);
                errors = true;
            } else {
                var q = 'label[for="' + selected.node().id + '"]';
                answer = d3.select(q).text();
                choice_id = selected.node().value;
                console.log('selected', selected);
                console.log('choice_id:', choice_id);
            }
            results.push({
                question: item.question,
                choice_id: choice_id,
                answer: answer
            });
            // d3.selectAll('form')
            //   .classed('was-validated', true);
            console.log(results);
        });

        console.log('errors:', errors);

        // event.preventDefault();
        // event.stopPropagation();

        if (errors === false) {
            // post data to the server
            var post_url = server_url + "/answers/";
            var post_data = {
                answers: results,
                task_completion_time: task_completion_time
                // log: log
            };
            fetch(post_url, {
                method: 'POST',
                body: JSON.stringify(post_data),
                credentials: 'include',
                headers: {'Content-Type': 'application/json'}
            }).then(res => res.json()).then(response => {
                console.log('POST response:', response);
                console.log('POST response.headers:', response.headers);
                // window.location.replace(server_url + "/tasks/?order=" + next_task_order);
                // window.location = server_url + "/tasks/?order=" + next_task_order;
                // window.location = response.completion_url;
                if (response['correct'] === true) {
                    // enable/show bottom card
                    d3.select('.success').style('display', 'block');
                    // d3.select('.success').node().scrollTo();
                    window.scrollTo(0,2000);
                    $('button.startShopButton').attr('disabled', null);
                } else {
                    if (response['attempt'] >= 2) {
                        alert('Unfortunately some of the answers were incorrect again. We kindly request that you return the study on prolific.');
                        d3.select('#submit-btn').attr('disabled', true);
                    } else {
                        alert('Unfortunately some of the answers were incorrect. You can try again one more time.');
                        // clear form
                        d3.selectAll('input:checked').each(function () {this.checked = false;});
                    }
                }
            }).catch(err => {
                console.log('POST error:', err);
            });
        }
    });

    $('button.skipVideoButton').click(function () {
 
        $('.main-loading').show()
        var tagging_images = [];
        var images_loaded = 0;
        for (var i = 0; i < 60; i+=1) {
            var image_url = `${server_url}/static/imagetagging/images/${i}.jpg`;
            console.log('loading:', image_url)
            tagging_images[i] = new Image();
            tagging_images[i].src = image_url;
            tagging_images[i].onload = function () {
                images_loaded += 1;
                var progress = `${images_loaded} items out of 60 loaded.`;
                $('.progress').html(progress);
                if (images_loaded >= 60) {
                    console.log('all loaded');

                    window.location.href = server_url + "/investment/";

                    // // console.log('username:', username);
                    // $.ajax({
                    //     type: "POST",
                    //     url: server_url + '/study/participant/start/',
                    //     success: function (data) {
                    //         console.log('start result:', data);
                    //         window.location.href = server_url + "/shop/";
                    //     },
                    //     error: function (data, msg, reason) {
                    //         console.log('error arguments', data.responseJSON);
                    //         var message = `Sorry, the system is currently not working. We are trying to fix it. ${data.responseJSON}`;
                    //         bootbox.alert(message);
                    //     }
                    // });
                    
                }
            };
        };
    
    });



    $('button.startStudyButton').click(function () {
 
        $('.main-loading').show()
        var tagging_images = [];
        var images_loaded = 0;
        for (var i = 0; i < 60; i+=1) {
            var image_url = `${server_url}/static/imagetagging/images/${i}.jpg`;
            console.log('loading:', image_url)
            tagging_images[i] = new Image();
            tagging_images[i].src = image_url;
            tagging_images[i].onload = function () {
                images_loaded += 1;
                var progress = `${images_loaded} items out of 60 loaded.`;
                $('.progress').html(progress);
                if (images_loaded >= 60) {
                    console.log('all loaded');
                    
                    window.location.href = server_url + "/investment/";
                    // // console.log('username:', username);
                    // $.ajax({
                    //     type: "POST",
                    //     url: server_url + '/study/participant/start/',
                    //     success: function (data) {
                    //         console.log('start result:', data);
                            
                    //     },
                    //     error: function (data, msg, reason) {
                    //         console.log('error arguments', data.responseJSON);
                    //         var message = `Sorry, the system is currently not working. We are trying to fix it. ${data.responseJSON}`;
                    //         bootbox.alert(message);
                    //     }
                    // });
                    
                }
            };
        };
    
    });

    

    $('.loading').hide();
    $('.main-loading').hide()
    $('.host').append('js says: ' + server_url);

    var start = performance.now();
    
}

d3.select(window).on("load", setup);
