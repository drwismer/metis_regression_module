# Predicting UFC Fight Scoring - Multivariate Linear Regression

## Abstract

The aim of this project is to explore available fight statistics to understand which statistics have the greatest impact on scoring decisions in the Ultimate Fighting Championship (UFC), a popular professional Mixed Martial Arts organization. Using historical fight statistics from [UFCStats.com](http://www.ufcstats.com/statistics/events/completed) and fight scoring data from [MMADecisions.com](http://mmadecisions.com/), I created a Multivariate Linear Regression model that accepts fight data (strikes, takedowns, submission attempts, control time, etc.) and predicts the score of the fight. In addition to evaluating the model's accuracy for predicting the correct score, I also evaluated the model's ability to pick the winner correctly.

## Design

It is important for the UFC (and other fight organizations) to understand how their judges are scoring fights based on what they see. The UFC has a hierarchy for how the winner of a round should be decided:

1. **Effective Striking and Grappling** - This is meant to be the deciding factor in the majority of rounds. Effective striking includes legal strikes (punches, kicks, knees, elbows) that inflict damage upon the opponent. Effective grappling includes successful takedowns, reversals, and submission attempts.
2. **Effective Aggression** - In the absence of a clear winner in the area of effective striking and grappling, effective aggression is the deciding factor. The round is awarded to the fighter who made the greatest attempt to finish the fight in the round.
3. **Effective Control of the Fight Area** - The final criterion for deciding a round winner, if there is no clear winner in striking/grappling or aggression, is control of the fight area. This encompasses pushing the pace of the fight and controlling the fight area (e.g. keeping the opponent up against the fence).

These judging guidelines are published and understood by judges, fighters, and fans. The guidelines help to create entertaining fights by aligning entertaining fight styles with a greater likelihood of winning fights. The scoring system rewards high output, high aggression, and fighting at a fast pace.

Understanding which fight statistics are impacting judging decisions through multivariate linear regression can help the UFC to evaluate whether their judging criteria is being followed appropriately. It can allow the organization to understand the true hierarchy of judging criteria at a deeper level (for example: "head strikes" vs. "effective striking"). An effective model could help with evaluating whether specific judges have been accurate over time and whether judging criteria should be amended to encourage different fight tactics for entertainment purposes.

#### *Limitations*

There are a few limitations in my predictive model:
1. **Striking and Grappling Effectiveness** - Certain aspects of a fight are not captured through the statistics available on UFCStats.com. For example, what constitues "effective striking" vs. ineffective striking? UFCStats.com tracks *significant* strikes for each fight, but even this determination can be subjective, and not all significant strikes are created equal. If one fighter lands several strikes throughout a round, and the other only lands two huge kicks that each knock their opponent to the ground, it may be unclear who should win that round. Significant grappling is even more difficult to quantify.
2. **Aggression and Control** - UFCStats.com provides control time as a tracked metric. But this may be the only indicator available that clearly relates to aggression and control. There are no other objective measures for quantifying how aggressive a fighter was during a round.
3. **Round Scoring** - My model looks at the fight statistcs for the entire fight rather than for individual rounds. In practice, judges score fights on a round by round basis, rather than the fight in its totality. However, the decision data is much more robust at the fight level, because MMADecisions.com includes media scoring at the fight level, but not at the round level. Creating a round-level scoring algorithm would be part of the roadmap for enhancing my predictive model.

## Data

The data for this project was scraped from UFCStats.com and MMADecisions.com and stored in a PostgreSQL database. I scraped all UFC data available, going back to 1997. I scraped decision data from MMADecisions.com for all fighters from 1/1/2010 through 5/31/2021. As such, the data for the regression model includes all UFC fights from 1/1/2020 through 5/31/2021 for which decision data was available on MMADecisions.com. If a fight ends in a knockout or submission, the judging data is not tracked on MMADecisions.com. Ultimately, my dataset includes 2,258 fights, which makes up 4,516 individual observations (one for each fighter in each fight). For each fight, I scraped fight statistics by round. For each fight statistic, I calculated the disparity between the fighters to feed to the model. For example, if fighter_1 landed 10 head strikes and fighter_2 landed 5 head strikes in a round, sig_head_land_disparity would be 5 for fighter_1 and -5 for fighter_2.

The following fight metrics were included prior to feature reduction:
- kd_disparity - Knockdowns disparity.
- sig_head_land_disparity - Significant head strikes landed disparity.
- sig_body_land_disparity -Significant body strikes landed disparity.
- sig_leg_land_disparity - Significant leg strikes landed disparity.
- sig_dist_land_disparity - Significant distance strikes landed disparity.
- sig_clinch_land_disparity - Significant clinch strikes landed disparity.
- sig_ground_land_disparity - Significant ground strikes landed disparity.
- sig_strike_land_disparity - Significant strikes landed disparity.
- total_strike_land_disparity - Total strikes landed disparity (including non-significant).
- total_strike_att_disparity - Total strikes attempted disparity.
- takedown_land_disparity - Takedowns landed disparity.
- takedown_att_disparity - Takedowns attempted disparity.
- sub_att_disparity - Submissions attempted disparity.
- reversals_disparity - Reversals disparity.
- ctrl_time_disparity - Control time disparity.

The fight statistics above were the starting place for the independent variables of the regression model. Some of these were trimmed during the feature selection process, which was conducted primarily by inspecting correlations and the variance inflation factor for my features. The dependent variable was based off of the MMADecisions.com data. Rather than using judge data only, I created a combined average score for a fight using all available judge and media scoring data. There are only 3 judges per fight, and their decisions are often highly criticized. In many cases, fight media is more knowledgeable than the judges of the fights. Including additional scores made for a more robust dependent variable.

## Algorithms

- **Train Test Split**
    - Rather than using the built in train test split functionality from sci-kit learn, I opted for a time based split. Rather than splitting randomly, this instead splits observations based on the date of the fight. This ensures that the record for fighter_1 and fighter_2 for a given fight will both be in the same dataset (train or test). This allows for comparing the predicted score for each fighter and declaring the winner based on the relative scores. Absent this methodology, there will be fights where only one of the two fighters is present in the testing data, which means that a different methodolgy must be used to determine if the model correctly predicted the winner. Specifically, if the actual and predicted per round scored are both over 9.5 or both under 9.5, the model would assume it has made a correct prediction. In addition to a more reasonable winner prediction methodology, this split avoids other issues that may arise with including one half of a fight in the training dataset and the other half in the testing dataset. The nature of the data is such that fighter_1 and fighter_2 are mirror images of each other, because the features reflect the difference between fighter_1 and fighter_2. Including fighter_1 in the training data and using that to predict fighter_2 in the testing data is not the most fair methodology. Given that there have been no significant rule changes over the course of my dataset timeline, a time-based split appears reasonable.
- **Feature Engineering**
    - I converted all fight statistics to disparity measures. In other words, if fighter_1 landed head strikes, and fighter_2 also landed head strikes, the record for fighter_1 would show significant head strikes landed *disparity*, calculated as fighter_1 head strikes less fighter_2 head strikes. The record for fighter_2 would show the inverse.
    - For the output variable, I combined judge scoring and media scoring to created combined_avg, which is a weighted average that gives equal weight to each judge and each media member.
    - Polynomial features - I explored the Seaborn pairplot for my reduced feature set, and there were no standouts that showed curvilinear relationships either with each other or with the dependent variable. I also imported **PolynomialFeatures** from the Sci-kit Learn library and tested the performance at different degrees. A degree of 2 increased the baseline Linear Regression model R-Squared from 0.6778 to 0.6904. A degree of 3 increased R-Squared to 0.6930. Given that the increase was minimal, and that their were no clear curvilinear relationships, I moved forward without polynomial features.
    - Feature interactions - I considered feature interactions, but in the context of scoring fights, there were no interactions that appeared relevant.
- **Feature Reduction**
    - *Correlation* - I plotted the fight statistics in a correlation heatmap using Seaborn. This gave me an initial idea of which features had high correlation and might need to be removed. I also saw which metrics correlated strongly with my independent variable(s). As an example, **takedown_att_disparity** (Takedowns Attempted) and **takedown_land_disparity** (Takedowns Landed) had highly negative correlations with most striking statistics, particularly sig_dist_land_disparity (Significant Distance Strikes Landed). This makes intuitive sense, because a fighter who attempts many more takedowns than their opponent is less likely to be focused on striking, especially striking from a distance rather than in the clinch or on the ground. Another example is **sig_strike_land_disparity**. This feature correlates highly with **sig_head_land_disparity** and **sig_distance_land_disparity**. This signifies that, historically, stiking the head and striking at a distance are the more common methods of striking in our dataset.
    - *Variance Inflation Factor (VIF)* - VIF is a tool for determining multicollinearity in a regression model. I ran VIF from the statsmodels library, which helped me to find features that were highly correlated and adversely impacting model performance. On my first run of the VIF, six features returned VIF of infinity. After removing colinear features, aided by the Seaborn heatmap, my second run of the VIF return VIF's under 5.0 (a typcial benchmark) for all features.
- **Regression**
    - *Model* - I used **LinearRegressor** from Sci-Kit Learn for my multivariate linear regression model. The model returned an **R-Squared of 0.7168**, but that doesn't tell the full story. The model also predicted the correct winner of the fight with **approximately 85.5% accuracy**.
    - *Regularization* - I tested **LASSO** and **Ridge** regression model from Sci-Kit Learn, and then had a neglibigle impact on R-Squared.
    - *Normalization, Standardization, Stochastic Gradient Descent, and Random Forest* - Normalizing with **MinMaxScaler** and standardizing with **StandardScaler** surprisingly had minimal impact on the performance of any model (other than SGDRegressor). I also tried implementing Stochastic Gradient Descent with the **SGDRegressor** from Sci-Kit Learn, but no amount of tuning returned significant improvement to the other linear regression models described above. Finally, I implemented **RandomForestRegressor**. Random Forest produced very strong results in cross validation, but less impressive results in testing. Even with hyperparameter tuning, it was difficult to avoid overfitting to the training data. The generalization error was by far the largest for Random Forest.
- **Validation**
    - Given that my dataset is relatively small, it was important to use cross validation to evaluate the different regression models. I implemented **cross_val_score** and **KFold** (5 folds) to validate. I also used **LassoCV** and **RidgeCV** for regularized regressions.
    - I also implemented simple validation manually, and the results were very similar. Random Forest performed the best in cross validation but Stochastic Gradient Descent performed best in simple validation, but all models were ultimately very close in all forms of validation and testing.

## Tools

- **Data Collection** - Scrapy
    - I used Scrapy, an object oriented programming web scraper, to scrape UFCStats.com and MMADecisions.com. Initializing a Scrapy project creates a package of modules that work together to scrape and store data. The majority of the work is done by the **spider** classes. These spiders each serve separate web scraping functions. I created a **PerformanceSpider** that scraped all available fight data from UFCStats.com. This spider grabbed all of the fight metrics and event information. I also created a **FighterSpider** that scraped the fighter information pages on UFCStats.com. Finally, I created a **DecisionSpider** that scraped MMADecisions.com, located the relevant fight found be the FighterSpider, and stored judging related information. The Scrapy package linked directly to my PostgreSQL database through SQL Alchemy.
- **Data Storage** - PostgreSQL and SQL Alchemy
    - SQL Alchemy was used to created and populate my Postgres database. The database includes tables for events, fights, rounds, round_results, and fighters. The judging information is stored in the round_results table, along with the fight metrics used in the regression model. I also used SQL Alchemy to query the database for data to be used in the model.
- **Data Manipulation** - Pandas and Numpy
- **Plotting** - Matplotlib, Seaborn, Axes3D
    - In addition to plotting typical scatter and box plots, I also used Axes3D to create a series of pictures that I turned into GIF's. These show four separate 3D projections displaying regressions with two independent variables and one dependent variable. This was just a fun visualization to include on my final slide, not integral to the project.
- **Model Building and Evaluation** - Sci-kit Learn and Statsmodels Module
    - I tested LinearRegression, Lasso, Ridge, SGDRegressor, and RandomForestRegressor from the Sci-kit Learn library. I tested each of these models using unaltered data, data normalized by MinMaxScaler, and data standardized by StandardScaler.
    - I evaluated the model using built in functionality from sci-kit learn and using variance_inflation_factor from the statsmodels module.
    - I used cross validation and K-fold from sci-kit learn to validate the models described above before moving on to the testing phase.
    - I calculated root mean squared error (RMSE), R-Squared, and the winner prediction accuracy for all models tested.

## Communication

I created slides that walk through my process for scraping data, choosing features, validating the various potential models, and ultimately selecting a final model. My ultimate choice was **Linear Regression using Normalized Data**. I chose Linear Regression because the model is very interpretable, and none of the fancier models provided a significant boost to performance. I prefer normalized features because normalizing allows for a more natural comparison of feature coefficients as a proxy of feature importance. 

After presenting my model selection, I provided a few key visualizations that demonstrate how the model works, how well it performs, and how it tends to fall short. I've included these below.

#### Model Performance
I ultimately moved three models forward to the testing phase. This visual shows how each performed based on R-Squared, RMSE, and prediction accuracy. It is important to note that, for evaluating the test data, I adjusted all predictions above 10.0 points per round back to 10.0, as this is the maximum number of points per round possible. This did not impact Random Forest, but had a 1-2% positive impact on Linear Regression and SGD Regression R-Squared and RMSE. Prediction Accuracy was not impacted.

<img src='images/pic - model performance.png' width=800>

#### Linear Regression Model 
I selected the Linear Regression model (with normalized data) as my winning model. This visual shows the coefficients for the features of the model, and these are very much in line with the prescribed judging criteria hierarchy.

<img src='images/pic - feature coef.png' width=800>

#### Winner Predictions 
This visual shows how well the winning model predicts the winner of a fight. A natural cutoff forms at 9.5 points per round. This is because, generally, one fighter gets 10 points per round and the other fighter gets 9 points per round. As such, the average points per round is 9.5. There are only two fighters in each fight, so if you perform above average, you win. If you perform below average, you lose. This means that, typically, when the predicted per round score and the actual per round score ***fall on the same side of 9.5***, the prediction will be correct.

<img src='images/pic - predictions.png' width=800>

#### Where the Model Fails
This visual shows the distributions of the features in observations where the model made correct or incorrect predictions. The feature distributions are noticeably closer in fights where the model got it wrong. This is because these features show disparities between the two fighters. When the disparities are smaller, that is an indicator that the fights were closely contested and more difficult to judge.

<img src='images/pic - feature dist.png' width=800>


