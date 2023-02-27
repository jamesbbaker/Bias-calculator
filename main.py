from flask import Flask, render_template, request
from scipy.stats import norm
import numpy as np
import plotly.express as px
import pandas as pd

import scipy.stats as stats

app = Flask(__name__)


@app.route('/binary', methods=['GET', 'POST'])
def non_binary():
  if request.method == 'POST':
    num_patients = int(request.form['num_patients'])
    sd = float(request.form['sd'])
    ctrl_rate = float(request.form['ctrl_rate'])
    treat_rate = float(request.form['treat_rate'])
    prev_n = int(request.form['prev_n'])

    sd, neg, sd_ml, neg_ml, num_patients, ctrl_rate, treat_rate, chart, chart_2, chart_2_ml = create_charts_nonbinary(
      num_patients, ctrl_rate, treat_rate, sd, prev_n)

    return render_template('nonbinary_trial_calc.html',
                           sd=sd,
                           neg=neg,
                           sd_ml=sd_ml,
                           neg_ml=neg_ml,
                           num_patients=num_patients,
                           prev_n=prev_n,
                           ctrl_rate=ctrl_rate,
                           treat_rate=treat_rate,
                           chart=chart,
                           chart_2=chart_2,
                           chart_2_ml=chart_2_ml)

  return render_template('nonbinary_trial_calc.html')


@app.route('/', methods=['GET', 'POST'])
def binary():
  if request.method == 'POST':
    num_patients = int(request.form['num_patients'])
    ctrl_rate = float(request.form['ctrl_rate'])
    treat_effect = ctrl_rate * float(request.form['treat_effect'])

    sd, neg, sd_ml, neg_ml, num_patients, ctrl_rate, treat_effect, chart, chart_2, chart_ml, chart_2_ml = create_charts(
      num_patients, ctrl_rate, treat_effect)

    return render_template('index.html',
                           sd=sd,
                           neg=neg,
                           sd_ml=sd_ml,
                           neg_ml=neg_ml,
                           num_patients=num_patients,
                           ctrl_rate=ctrl_rate,
                           treat_effect=treat_effect,
                           chart=chart,
                           chart_2=chart_2,
                           chart_ml=chart_ml,
                           chart_2_ml=chart_2_ml)

  return render_template('index.html')


def create_charts_nonbinary(num_patients, ctrl_rate, treat_rate, sd, prev_n):

  new_sd = sd * np.sqrt(2) * np.sqrt(prev_n / num_patients)

  ctrl_mean = ctrl_rate
  ctrl_sd = new_sd
  treat_mean = treat_rate
  treat_sd = new_sd

  x = np.linspace(0, 100, 10001)
  ctrl_y = norm.pdf(x, ctrl_rate, new_sd)
  treat_y = norm.pdf(x, treat_rate, new_sd)

  x_min = min(ctrl_mean - 2 * ctrl_sd, treat_mean - 2 * treat_sd)
  x_max = max(ctrl_mean + 2 * ctrl_sd, treat_mean + 2 * treat_sd)

  chart = px.line(
    x=x,
    y=ctrl_y,
    title=
    'Probability distribution of outcome rate of both Treatment and Control arms',
    range_x=[0, x_max])
  chart.add_scatter(x=x,
                    y=ctrl_y,
                    mode='lines',
                    name='Control Arm',
                    line=dict(color='blue'))
  chart.add_scatter(x=x, y=treat_y, mode='lines', name='Treatment Arm')

  chart.update_layout(
    annotations=[
      dict(x=treat_mean,
           y=max(treat_y),
           text=f'Treatment mean: {treat_mean:.2f}',
           showarrow=True,
           font=dict(size=16)),
      dict(x=ctrl_mean,
           y=max(ctrl_y),
           text=f'Control mean: {ctrl_mean:.2f}',
           showarrow=True,
           font=dict(size=16)),
      dict(
        x=ctrl_mean,
        y=0,  #max(ctrl_y) + .05,
        text=
        'After randomizing across subgroups, trials often assume a placebo outcome rate and do not account for this variation',
        showarrow=False,
        font=dict(size=16, family='Arial', color='black'))
    ],
    legend=dict(
      x=.8,
      y=1,
      traceorder="normal",
      font=dict(family="sans-serif", size=12, color="black"),
      bgcolor="LightSteelBlue",
      bordercolor="Black",
      borderwidth=2,
    ))

  chart.add_shape(type='line',
                  y0=max(ctrl_y),
                  y1=0,
                  x0=ctrl_mean,
                  x1=ctrl_mean,
                  line=dict(color='gray', dash='dot'))

  # 1) y ticks should be %s
  chart.update_layout(yaxis=dict(tickformat=".0%"))
  # 2) y axis label should be 'Probability distribution of trials'
  chart.update_layout(yaxis_title="Probability distribution of trials")

  # 3) x label should be 'Rate of Suboptimal Outcome'
  chart.update_layout(xaxis_title="Rate of Suboptimal Outcome")

  #CHART 2

  x_2 = np.linspace(-15, 15, num=30001)

  sd_2 = np.sqrt(treat_sd * treat_sd + ctrl_sd * ctrl_sd)

  diff = treat_mean - ctrl_mean
  diff_y = norm.pdf(x_2, diff, sd_2)

  alpha = 0.05
  z_score = stats.norm.ppf(alpha/2)
  se = ((ctrl_sd ** 2 / (num_patients / 2)) + (treat_sd ** 2 / (num_patients / 2) )) ** 0.5 # standard error
  
  required_effect = z_score * se *-1

  print('T-critical:')
  print(z_score)
  print('effect-size:')
  print(required_effect)

  x_min_2 = diff - 2 * sd_2
  x_max_2 = diff + 2 * sd_2

  neg = sum(diff_y[x_2 >= -0.9]) / 10

  chart_2 = px.line(
    x=x_2,
    y=diff_y,
    title=
    'Taking the difference of these 2 distributions, we can model out the probability trial bias will lead to false negative (or positive) results',
    range_x=[x_min_2, x_max_2])
  chart_2.add_scatter(x=x_2,
                      y=diff_y,
                      mode='lines',
                      name='Difference between trial and control arms',
                      line=dict(color='blue'))
  chart_2.add_scatter(x=x_2[x_2 >= -0.9],
                      y=diff_y[x_2 >= -0.9],
                      fill='tozeroy',
                      mode='none',
                      name='Trials with negative treatment effect',
                      line=dict(color='blue'))
  chart_2.add_annotation(
    x=-0.9,
    y=0,
    text='Probability trial does not demonstrate stated efficacy of -0.9 (-30%) (95% CI, 0.05 alpha): {}%'.
    format(round(neg, 2)),
    font=dict(size=16))

  chart_2.add_annotation(
    x=diff,
    y=max(diff_y) * .5,
    text='Expected treatment effect on outcomes: {}%'.format(
      round(diff / ctrl_mean * 100, 2)),
    font=dict(size=16))

  chart_2.add_shape(type='line',
                    y0=0,
                    y1=max(diff_y[x_2 >= -0.9]),
                    x0=-0.9,
                    x1=-0.9,
                    line=dict(color='gray', dash='dot'))

  chart_2.add_shape(type='line',
                    y0=0,
                    y1=max(diff_y),
                    x0=diff,
                    x1=diff,
                    line=dict(color='gray', dash='dot'))

  chart_2.update_layout(yaxis=dict(tickformat=".0%"),
                        yaxis_title="Probability distribution of trials",
                        xaxis_title="Difference in Rate of Suboptimal Outcome",
                        legend=dict(
                          x=0,
                          y=1,
                          traceorder="normal",
                          font=dict(family="sans-serif",
                                    size=12,
                                    color="black"),
                          bgcolor="LightSteelBlue",
                          bordercolor="Black",
                          borderwidth=2,
                        ))

  #CHART 3 ML

  reduction_in_var = 0.5
  ctrl_sd_ml = new_sd * np.sqrt(reduction_in_var)
  treat_sd_ml = new_sd * np.sqrt(reduction_in_var)

  x_2_ml = np.linspace(-15, 15, num=30001)

  diff_ml = treat_mean - ctrl_mean

  sd_2_ml = np.sqrt(treat_sd_ml * treat_sd_ml +
                    ctrl_sd_ml * ctrl_sd_ml)

  diff_y_ml = norm.pdf(x_2_ml, diff_ml, sd_2_ml)

  neg_ml = sum(diff_y_ml[x_2_ml >= required_effect * -1]) / 10

  chart_2_ml = px.line(
    x=x_2_ml,
    y=diff_y_ml,
    title=
    'ML risk assessment included as a subgroup in randomization process can reduce bias up to 50% (COVID example)',
    range_x=[x_min_2, x_max_2])
  chart_2_ml.add_scatter(x=x_2_ml,
                         y=diff_y_ml,
                         mode='lines',
                         name='Difference between trial and control arms',
                         line=dict(color='blue'))
  chart_2_ml.add_scatter(x=x_2_ml[x_2_ml >= required_effect * -1],
                         y=diff_y_ml[x_2_ml >= required_effect * -1],
                         fill='tozeroy',
                         mode='none',
                         name='Trials with negative treatment effect',
                         line=dict(color='blue'))

  chart_2_ml.add_annotation(
    x=required_effect * -1,
    y=0,
    text='Probability trial does not demonstrate positive efficacy (95% CI, 0.05 alpha): {}%'.
    format(round(neg_ml, 2)),
    font=dict(size=16))

  chart_2_ml.add_annotation(
    x=diff_ml,
    y=max(diff_y_ml) * .5,
    text='Expected treatment effect on outcomes: {}%'.format(
      round(diff_ml / ctrl_mean * 100, 2)),
    font=dict(size=16))

  chart_2_ml.add_shape(type='line',
                       y0=0,
                       y1=max(diff_y_ml[x_2_ml >= required_effect * -1]),
                       x0=required_effect * -1,
                       x1=required_effect * -1,
                       line=dict(color='gray', dash='dot'))

  chart_2_ml.add_shape(type='line',
                       y0=0,
                       y1=max(diff_y_ml),
                       x0=diff,
                       x1=diff,
                       line=dict(color='gray', dash='dot'))

  chart_2_ml.update_layout(legend=dict(
    x=0,
    y=1,
    traceorder="normal",
    font=dict(family="sans-serif", size=12, color="black"),
    bgcolor="LightSteelBlue",
    bordercolor="Black",
    borderwidth=2,
  ))

  chart_2_ml.update_layout(yaxis=dict(tickformat=".0%"))
  chart_2_ml.update_layout(yaxis_title="Probability distribution of trials")
  chart_2_ml.update_layout(
    xaxis_title="Difference in Rate of Suboptimal Outcome")

  sd = sd
  neg = neg
  sd_ml = ctrl_sd_ml
  neg_ml = neg_ml
  num_patients = num_patients
  chart = chart.to_html(full_html=False)
  chart_2 = chart_2.to_html(full_html=False)
  chart_2_ml = chart_2_ml.to_html(full_html=False)

  return sd, neg, sd_ml, neg_ml, num_patients, ctrl_rate, treat_rate, chart, chart_2, chart_2_ml


def create_charts(num_patients, ctrl_rate, treat_effect):

  ctrl_mean = ctrl_rate
  ctrl_sd = np.sqrt((ctrl_mean * (1 - ctrl_mean)) / (num_patients * 0.5))
  treat_mean = ctrl_rate + treat_effect
  treat_sd = np.sqrt((treat_mean * (1 - treat_mean)) / (num_patients * 0.5))

  ctrl_dist = norm(ctrl_mean, ctrl_sd)
  treat_dist = norm(treat_mean, treat_sd)

  x = np.linspace(-1, 1, num=20001)
  ctrl_y = ctrl_dist.pdf(x)
  treat_y = treat_dist.pdf(x)

  x_min = min(ctrl_mean - 3 * ctrl_sd, treat_mean - 3 * treat_sd)
  x_max = max(ctrl_mean + 3 * ctrl_sd, treat_mean + 3 * treat_sd)

  chart = px.line(
    x=x,
    y=ctrl_y / 100,
    title='Probability Distributions of Control Arm vs Treatment Arm',
    range_x=[x_min, x_max])
  chart.add_scatter(x=x,
                    y=ctrl_y / 100,
                    mode='lines',
                    name='Control Arm',
                    line=dict(color='blue'))
  chart.add_scatter(x=x, y=treat_y / 100, mode='lines', name='Treatment Arm')

  chart.update_layout(annotations=[
    dict(x=treat_mean,
         y=max(treat_y) / 100,
         text=f'Treatment mean: {treat_mean:.3f}',
         showarrow=True),
    dict(x=ctrl_mean,
         y=max(ctrl_y) / 100,
         text=f'Control mean: {ctrl_mean:.3f}',
         showarrow=True)
  ],
                      legend=dict(
                        x=0,
                        y=1,
                        traceorder="normal",
                        font=dict(family="sans-serif", size=12, color="black"),
                        bgcolor="LightSteelBlue",
                        bordercolor="Black",
                        borderwidth=2,
                      ))

  # 1) y ticks should be %s
  chart.update_layout(yaxis=dict(tickformat=".0%"))
  # 2) y axis label should be 'Probability distribution of trials'
  chart.update_layout(yaxis_title="Probability distribution of trials")
  # 3) x label should be 'Rate of Suboptimal Outcome'
  chart.update_layout(xaxis_title="Rate of Suboptimal Outcome")

  #CHART 2

  diff = treat_mean - ctrl_mean
  x_2 = np.linspace(-1.5, .5, num=20001)

  diff_sd = np.sqrt(treat_sd * treat_sd + ctrl_sd * ctrl_sd)

  diff_y = norm.pdf(x_2, diff, diff_sd)

  x_min_2 = diff - 3 * diff_sd
  x_max_2 = diff + 3 * diff_sd

  neg = sum(diff_y[x_2 >= 0]) / 100

  print(sum(diff_y))

  chart_2 = px.line(
    x=x_2,
    y=diff_y,
    title=
    'Probability Distribution of Treatment Effect on Suboptimal Outcome (<0 is a decrease in suboptimal outcomes)',
    range_x=[x_min_2, x_max_2])
  chart_2.add_scatter(x=x_2,
                      y=diff_y,
                      mode='lines',
                      name='Difference between trial and control arms',
                      line=dict(color='blue'))
  chart_2.add_scatter(x=x_2[x_2 >= 0],
                      y=diff_y[x_2 >= 0],
                      fill='tozeroy',
                      mode='none',
                      name='Trials with negative treatment effect',
                      line=dict(color='blue'))

  chart_2.add_shape(type='line',
                    y0=1,
                    y1=0,
                    x0=0,
                    x1=0,
                    line=dict(color='gray', dash='dot'))

  chart_2.add_annotation(
    x=0,
    y=.5,
    text='Percentage of trials with negative treatment effect: {}%'.format(
      round(neg, 2)))

  chart_2.update_layout(yaxis=dict(tickformat=".0%"),
                        yaxis_title="Probability distribution of trials",
                        xaxis_title="Difference in Rate of Suboptimal Outcome",
                        legend=dict(
                          x=0,
                          y=1,
                          traceorder="normal",
                          font=dict(family="sans-serif",
                                    size=12,
                                    color="black"),
                          bgcolor="LightSteelBlue",
                          bordercolor="Black",
                          borderwidth=2,
                        ))

  #CHART 3 ML

  reduction_in_var = 0.6
  ctrl_sd_ml = np.sqrt(
    (ctrl_mean * (1 - ctrl_mean) * reduction_in_var) / (num_patients * .5))
  treat_sd_ml = np.sqrt(
    (treat_mean * (1 - treat_mean) * reduction_in_var) / (num_patients * .5))

  ctrl_dist_ml = norm(ctrl_mean, ctrl_sd_ml)
  treat_dist_ml = norm(treat_mean, treat_sd_ml)

  x_ml = np.linspace(-1, 1, num=20001)
  ctrl_y_ml = ctrl_dist_ml.pdf(x_ml)
  treat_y_ml = treat_dist_ml.pdf(x_ml)

  x_min_ml = min(ctrl_mean - 3 * ctrl_sd_ml, treat_mean - 3 * treat_sd_ml)
  x_max_ml = max(ctrl_mean + 3 * ctrl_sd_ml, treat_mean + 3 * treat_sd_ml)

  chart_ml = px.line(
    x=x_ml,
    y=ctrl_y_ml / 100,
    title=
    'Probability Distributions of Control Arm vs Treatment Arm (ML risk score reduces suboptimal outcome variance between arms by 40%)',
    range_x=[x_min_ml, x_max_ml])
  chart_ml.add_scatter(x=x_ml,
                       y=ctrl_y_ml / 100,
                       mode='lines',
                       name='Control Arm',
                       line=dict(color='blue'))
  chart_ml.add_scatter(x=x_ml,
                       y=treat_y_ml / 100,
                       mode='lines',
                       name='Treatment Arm')

  chart_ml.update_layout(annotations=[
    dict(x=treat_mean,
         y=max(treat_y_ml) / 100,
         text=f'Treatment mean: {treat_mean:.3f}',
         showarrow=True),
    dict(x=ctrl_mean,
         y=max(ctrl_y_ml) / 100,
         text=f'Control mean: {ctrl_mean:.3f}',
         showarrow=True)
  ],
                         legend=dict(
                           x=0,
                           y=1,
                           traceorder="normal",
                           font=dict(family="sans-serif",
                                     size=12,
                                     color="black"),
                           bgcolor="LightSteelBlue",
                           bordercolor="Black",
                           borderwidth=2,
                         ))

  # 1) y ticks should be %s
  chart_ml.update_layout(yaxis=dict(tickformat=".0%"))
  # 2) y axis label should be 'Probability distribution of trials'
  chart_ml.update_layout(yaxis_title="Probability distribution of trials")
  # 3) x label should be 'Rate of Suboptimal Outcome'
  chart_ml.update_layout(xaxis_title="Rate of Suboptimal Outcome")

  #CHART 4 ML

  x_2_ml = np.linspace(-1.5, .5, num=20001)

  diff_ml = treat_mean - ctrl_mean

  sd_2_ml = np.sqrt(treat_sd_ml * treat_sd_ml + ctrl_sd_ml * ctrl_sd_ml)

  diff_y_ml = norm.pdf(x_2_ml, diff_ml, sd_2_ml)

  x_min_2_ml = diff_ml - 3 * sd_2_ml
  x_max_2_ml = diff_ml + 3 * sd_2_ml

  neg_ml = sum(diff_y_ml[x_2_ml >= 0]) / 100

  chart_2_ml = px.line(
    x=x_2_ml,
    y=diff_y_ml / 100,
    title=
    'Probability Distribution of Treatment Effect on Suboptimal Outcome with ML (<0 is a decrease in suboptimal outcomes)',
    range_x=[x_min_2_ml, x_max_2_ml])
  chart_2_ml.add_scatter(x=x_2_ml,
                         y=diff_y_ml / 100,
                         mode='lines',
                         name='Difference between trial and control arms',
                         line=dict(color='blue'))
  chart_2_ml.add_scatter(x=x_2_ml[x_2_ml >= 0],
                         y=diff_y_ml[x_2_ml >= 0] / 100,
                         fill='tozeroy',
                         mode='none',
                         name='Trials with negative treatment effect',
                         line=dict(color='blue'))

  chart_2_ml.add_shape(type='line',
                       y0=1,
                       y1=0,
                       x0=0,
                       x1=0,
                       line=dict(color='gray', dash='dot'))

  chart_2_ml.add_annotation(
    x=0,
    y=.5,
    text='Percentage of trials with negative treatment effect: {}%'.format(
      round(neg_ml, 2)))

  chart_2_ml.update_layout(legend=dict(
    x=0,
    y=1,
    traceorder="normal",
    font=dict(family="sans-serif", size=12, color="black"),
    bgcolor="LightSteelBlue",
    bordercolor="Black",
    borderwidth=2,
  ))

  chart_2_ml.update_layout(yaxis=dict(tickformat=".0%"))
  chart_2_ml.update_layout(yaxis_title="Probability distribution of trials")
  chart_2_ml.update_layout(
    xaxis_title="Difference in Rate of Suboptimal Outcome")

  sd = (ctrl_sd + treat_sd) / 2
  neg = neg
  sd_ml = (ctrl_sd_ml + treat_sd_ml) / 2
  neg_ml = neg_ml
  num_patients = num_patients
  ctrl_rate = round(ctrl_rate, 2)
  treat_effect = round(treat_effect / ctrl_rate, 2)
  chart = chart.to_html(full_html=False)
  chart_2 = chart_2.to_html(full_html=False)
  chart_ml = chart_ml.to_html(full_html=False)
  chart_2_ml = chart_2_ml.to_html(full_html=False)

  return sd, neg, sd_ml, neg_ml, num_patients, ctrl_rate, treat_effect, chart, chart_2, chart_ml, chart_2_ml


app.run(host='0.0.0.0', port=81)
