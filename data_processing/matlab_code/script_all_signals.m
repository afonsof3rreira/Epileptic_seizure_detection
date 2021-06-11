
% vector with the names of the .csv files
name_vec = ["afonso_seizure2_30s_nonfilt.csv", "afonso_videogame_nonfilt.csv", "afonso_jumpingrope_nonfilt.csv", "afonso_runningaround_nonfilt.csv"];

% T(:,:) = " ";

for i = 1: length(name_vec)
    mat = readtable(name_vec(i));
    T(i, :, :) = table2array(readtable(name_vec(i)));
end

%% computing the acc magnitudes of the acquisitions

times = T(:, :, 2);
acc = T(:, :, 3:5);
pulse = T(:, :, 6);
eda = T(:, :, 7);

acc_mag = zeros(size(T, 1), size(T, 2));

% compute magnitudes for acc of every recording
for i = 1:size(T, 1)
    temp = zeros(1, size(T, 2));
    for j = 1:size(T, 2)
        temp(1, j) = sqrt(acc(i, j, 1)^2 + acc(i, j, 2)^2 + acc(i, j, 3)^2);
    end
    acc_mag(i, :) = temp(1, :);
end

%% plotting acc magnitudes

figure()
subplot(4, 1, 1)
plot(times(1, 1:4500)./1000, acc_mag(1, 1:4500)); grid on; grid minor;
title('seizure');
subplot(4, 1, 2)
plot(times(2, :)./1000, acc_mag(2, :)); grid on; grid minor;
title('playing video games');
subplot(4, 1, 3)
plot(times(3, :)./1000, acc_mag(3, :)); grid on; grid minor;
title('rope jumping');
subplot(4, 1, 4)
plot(times(4, :)./1000, acc_mag(4, :)); grid on; grid minor;
title('running');

%% plotting the FFTs of the acc magnitudes

p_IMF2PFFT_iasb(acc_mag,100, 'example', 'example', 'example');


%% (used in the heart rate experiments) removing ECG and background noise artefacts

X = pulse;
[~, maximas, minimas, ~] = findextremas(X);
peak_locs = maximas(:, 2) > 0.6;
maximas = maximas(peak_locs, :);
instant_rate = zeros(size(maximas, 1), size(maximas, 2));
sum_period = 0;
min_freq = 100;
max_freq = 0;

sf = 100;
for i = 1 : size(maximas, 1) - 1
    period_i = (maximas(i + 1, 1) - maximas(i, 1)) * (1/sf);
    if 1/period_i > max_freq
        max_freq = 1/period_i;
    end
    if 1/period_i < min_freq
        min_freq = 1/period_i;
    end
    sum_period = sum_period + period_i;
    instant_rate(i, 1) = maximas(i, 1);
    if (60 / period_i) > 140.0
        instant_rate(i, 2) = 70.0;
    else
        instant_rate(i, 2) = (60 / period_i);
    end
    
end
instant_rate(end, 1) = maximas(end, 1);
instant_rate(end, 2) = 70;

avg_freq = 1 / (sum_period / (size(maximas, 1) - 1));
disp(min_freq * 60);
disp(avg_freq * 60) % x 60 for average detected bpm
disp(max_freq * 60);
% between 1 and 1.17 Hz

instant_rate(:, 2) = lowpass(instant_rate(:, 2), 0.3);

% t_vec = 0: 1/sf : length(X);

figure();
yyaxis left;
plot(X); axis tight;
hold on;
yyaxis right;

plot(instant_rate(:, 1), instant_rate(:, 2)); % 'Color', [0.4660 0.6740 0.1880]);
% scatter(maximas(:, 1), maximas(:, 2));

hold off;
