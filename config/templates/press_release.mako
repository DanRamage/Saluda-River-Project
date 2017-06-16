<!DOCTYPE html>

<html lang="en">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link href="http://dev.howsmyscriver.org/static/css/bootstrap/css/bootstrap.min.css" rel="stylesheet">
      <link href="http://dev.howsmyscriver.org/static/css/bootstrap/css/bootstrap-theme.min.css" rel="stylesheet">

      <title>Saluda River Coalition Test Results</title>
    </head>
    <body>
      <div class="container">
        <H2>Saluda River Coalition Test Results</H2>
        <H3>Sampling Date: ${sampling_date}</H3>
        <p>
          On ${sampling_date}, water quality samples at sites:
          <span>
            % for site_data in failed_sites:
            <span><h4>${site_data['test_result'].name} - ${site_data['wq_site'].description}</h4></span>
            % endfor
          </span>
          were above the state standard for E. coli. See <a href="http://dev.howsmyscriver.org/saluda">Hows My SC River</a> for the most current data.
        </p>
        <p>
          As a reminder, all samples are a snapshot in time and the water quality in a flowing river changes frequently.
          It is also important to note that it takes 24 hours to analyze a sample.
          This enhanced seasonal sampling is sponsored by Lower Saluda River Coalition for the months May through September <a href="http://dev.howsmyscriver.org/saluda#moreInformation"> About Sampling </a>.
        </p>
        <p>
          Any questions can be sent <a href="mailto:${feedback_email}?subject=[Saluda River Information Request]" target="_top"> here </a>.
        </p>
      </div>
    </body>
</html>
