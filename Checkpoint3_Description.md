# Checkpoint 3 Description

This document should have three sections:

1. Analysis approach
    1. Describe the type of analysis that seems most promising for your project: supervised learning, unsupervised learning, or text analysis.  
    2. Discuss how you will implement the analysis in a paragraph form. Be sure to include information to help others repeat your analysis including your random seed, the training approach (cross validation or training/testing) and ratio of data, the hyperparameters you plan to optimize and how you will approach that optimization, planned feature engineering steps (e.g., sclaing, UMAP, PCA, dummy coding) and any other pertinent information.
2. Baseline model fit:
    1. Construct a simple model. If you create a supervised learning model, use tidymodels to perform the steps outlined in the demonstration code and exercise (use the soccer relegation code for this).
    2. Start this model by making it as simple as possible: use a few features and linear or logistic regression.
3. Advanced model fit
    1. Once the baseline model works, expand to another model or add more features.
    2. Make sure to follow the process you described in your analysis approach above and share the relevant prediction performance metrics. (note: If you are using unsupervised learning you should use the tidyclust approach and if you are performing text analysis you should use the tidytext approach).
4. Model evaluation:
    1. Describe the model performance in general and instances where it performs poorly.
    2. 1. Compare your simple and more complex model. Try to use visualizations to understand your predictions/cluster performance and any systematic errors.
