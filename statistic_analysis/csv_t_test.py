
from scipy.stats import ttest_ind, mannwhitneyu
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

# inverted car puzzle durations
# data_tailored = """480.0078 178.7715 480.0111 83.90610000000 430.0096 371.1083 92.4762 154.4904000000 205.0038 149.9879"""
# data_untailored = """257.0053 480.009 370.4254 368.0128 365.009 398.9999 292.7909 240.6936 182.6745 480.010"""

data_tailored = """480.0078 178.7715 480.0111 83.90610000000 430.0096 371.1083 92.4762 154.4904000000 205.0038 149.9879"""
data_untailored = """257.0053 480.009 370.4254 368.0128 365.009 398.9999 292.7909 240.6936 182.6745 480.010"""

data_tailored = list(map(float, data_tailored.split()))
data_untailored = list(map(float, data_untailored.split()))
print(data_tailored, data_untailored)

# Sample data (replace these with your actual data)
group1 = np.array(data_tailored)
group2 = np.array(data_untailored)
# Normality test
# Shapiro-Wilk test
shapiro_group1 = stats.shapiro(group1)
shapiro_group2 = stats.shapiro(group2)

print("Shapiro-Wilk Test for Group 1: W = {}, p-value = {}".format(shapiro_group1[0], shapiro_group1[1]))
print("Shapiro-Wilk Test for Group 2: W = {}, p-value = {}".format(shapiro_group2[0], shapiro_group2[1]))

# Q-Q plots
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
stats.probplot(group1, dist="norm", plot=plt)
plt.title("Q-Q plot for Group 1")

plt.subplot(1, 2, 2)
stats.probplot(group2, dist="norm", plot=plt)
plt.title("Q-Q plot for Group 2")

plt.show()

# Variance equality test
# Levene's test
levene_test = stats.levene(group1, group2)

print("Levene's Test: W = {}, p-value = {}".format(levene_test[0], levene_test[1]))

# Independent Samples t-test (assuming equal variances)
t_statistic, p_value = ttest_ind(group1, group2, equal_var=True)

# Welch’s t-test (assuming unequal variances)
t_statistic_welch, p_value_welch = ttest_ind(group1, group2, equal_var=False)
print("\n")
print("T-test assuming equal variances: t = {}, p-value = {}".format(t_statistic, p_value))
print("Welch's T-test assuming unequal variances: t = {}, p-value = {}".format(t_statistic_welch, p_value_welch))
print("\n")

# Performing the Mann-Whitney U Test -> non-parametric test - normality assumption is violated
u_statistic, p_value_mannwhitney = mannwhitneyu(group1, group2, alternative='two-sided')
print("---- if Shapiro-Wilk Test for both groups has p-value < 0.05, then use Mann-Whitney U Test:")
print(f"Mann-Whitney U Test: U = {u_statistic}, p-value = {p_value_mannwhitney}")

#######################################
# t_stat, p_value = ttest_ind(data_tailored, data_untailored)
# print(f"t-statistic: {t_stat}, p-value: {p_value}")

