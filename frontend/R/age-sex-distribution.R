age_file <- list.files(tabular_dir, full.names = T) %>% str_subset(".*_demographics")
if (length(age_file) == 0) {
  warning("No WorldPop age distribution file")
} else if (length(age_file) > 1) {
  warning("Too many files match .*_demographics pattern")
} else {
  pop_dist_group_wp <- read_csv(age_file, col_types = "ffd") %>% 
    rename(Age_Bracket = age_group, Sex = sex, Count = population) %>%
    mutate(Sex = fct_recode(Sex, "Female" = "f", "Male" = "m")) %>%
    mutate(Age_Bracket = forcats::fct_collapse(Age_Bracket, "0-4" = c("0-1", "1-4"))) %>%
    group_by(Age_Bracket, Sex) %>% summarize(Count = sum(Count), .groups = "drop") %>%
    # mutate(Age_Bracket = factor(Age_Bracket, levels = unique(Age_Bracket))) %>%
    mutate(Percentage = Count/sum(Count)) %>%
    group_by(Sex) %>%
    mutate(
      Sexed_Percent = Count/sum(Count),
      Sexed_Percent_cum = cumsum(Sexed_Percent)) %>% 
    ungroup()
  
  # Print WorldPop age-sex distribution table (OUTPUT)
  # print_paged_df(pop_dist_group_wp)
  
  pop_age_sex_plot <- ggplot(pop_dist_group_wp, aes(x = Age_Bracket, y = Percentage, fill = Sex)) +
    # geom_bar(stat = "identity", position = "dodge2") + 
    geom_col(position = "dodge") + 
    labs(title = paste("Population distribution in", city, "by sex"),
         y = "Percentage", x = "Age Bracket", fill = "") +
    theme_minimal() +
    theme(legend.position = "none",
          legend.key.height = unit(1/8, "in"),
          axis.line = element_line(linewidth = .5, color = "black"),
          panel.grid.major.x = element_blank(),
          panel.grid.minor.x = element_blank(),
          panel.grid.major.y = element_line(linewidth = .125, color = "dark gray"),
          panel.grid.minor.y = element_line(linewidth = .125, linetype = 2, color = "dark gray")
          # panel.grid.major = element_line(linewidth = .125, color = "dark gray"),
          # panel.grid.minor = element_line(linewidth = .125, linetype = 2, color = "dark gray")
    ) + 
    scale_y_continuous(breaks = seq(0, .2, .01),
                       labels = scales::percent_format(accuracy = 1),
                       limits = c(0, ceiling(max(pop_dist_group_wp$Percentage) * 100) /100),
                       expand = c(0,0)) #+
  # scale_fill_manual(values = hues)
  
  # Print WorldPop age-sex distribution plot (OUTPUT)
  # ggplot2:::print.ggplot(pop_age_sex_plot)
  ggsave(file.path(charts_dir, "world-pop-age-sex.png"), plot = pop_age_sex_plot, device = "png",
         width = 8, height = 6.84, units = "in", dpi = "print")
  
  # under5 <- pop_dist_group_wp %>% 
  #   filter(Age_Bracket %in% c("0-4")) %>% summarize(across(c(Count, Percentage), sum))
  # youth <- pop_dist_group_wp %>% 
  #   filter(Age_Bracket %in% c("15-19", "20-24")) %>% summarize(across(c(Count, Percentage), sum))
  # working_age <- pop_dist_group_wp %>% 
  #   filter(Age_Bracket %in% c("15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64")) %>% summarize(across(c(Count, Percentage), sum))
  # elderly <- pop_dist_group_wp %>% 
  #   filter(Age_Bracket %in% c("60-64", "65-69", "70-74", "75-79", "80+")) %>% summarize(across(c(Count, Percentage), sum))
  # sex_totals <-  pop_dist_group_wp %>% 
  #   group_by(Sex) %>% summarize(across(c(Count, Percentage), sum))
  # female_pct <- sex_totals[which(sex_totals$Sex == "Female"), 3]
  # sex_ratio <- (1 - female_pct) / female_pct * 100
  # reproductive_age <-  pop_dist_group_wp %>% 
  #   filter(Sex == "Female", Age_Bracket %in% c("15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49")) %>% summarize(across(c(Count, Sexed_Percent), sum))
  
  # if (!in_oxford) {
  #   # Print age distribution if not in Oxford (OUTPUT)
  #   pop_dist_group_wp %>% group_by(Age_Bracket) %>% 
  #     summarize(Percentage = sum(Percentage)) %>%
  #     mutate(cumpct = cumsum(Percentage)) %>%
  #     print_paged_df()
  # }
  
  # # Print demographic stats (OUTPUT)
  # print_text(paste("under5:", under5$Percentage %>% {scales::label_percent()(.)}))
  # print_text(paste("youth (15-24):", youth$Percentage %>% {scales::label_percent()(.)}))
  # print_text(paste("working_age (15-64):", working_age$Percentage %>% {scales::label_percent()(.)}))
  # print_text(paste("elderly (60+):", elderly$Percentage %>% {scales::label_percent()(.)}))
  # print_text(paste("reproductive_age, percent of women (15-50):", reproductive_age$Sexed_Percent %>% {scales::label_percent()(.)}))
  # print_text(paste("sex_ratio:", round(sex_ratio, 2), "males to 100 females"))
}
