project_root = fileparts(fileparts(mfilename('fullpath')));
matlab_root = fullfile(project_root, 'reference_plane_matlab_Tan');
addpath(matlab_root);

if ~exist('output_root', 'var')
    error('output_root variable is required');
end
if ~exist(output_root, 'dir')
    mkdir(output_root);
end

C = 3e8;
R = 0.6;
X0 = 0.3;
theta_h = 30 / 180 * pi;
fmin = 30e9;
fmax = 39e9;
Nr = 181;
Kw = linspace(4 * pi * fmin / C, 4 * pi * fmax / C, Nr);
dh = 0.004;
h = (-0.08:dh:0.08);
Nh = length(h);
Kz = (2 * pi / (Nh * dh)) * ((-floor(Nh/2)):(ceil(Nh/2)-1));
Na = 91;
u = linspace(-15 / 180 * pi, 15 / 180 * pi, Na);
Kwz = sqrt(max((ones(Nh, 1) * Kw).^2 - (Kz.' * ones(1, Nr)).^2, 0));

s3 = zeros(Na, Nr, Nh);
rho_tar = 0.15;
z_tar = 0.0;
rn = sqrt(ones(Nh, 1) * (R^2 + rho_tar^2 - 2 * R * rho_tar * cos(u)) + ((z_tar - h).^2).' * ones(1, Na));
for jj = 1:Nh
    Rn = rn(jj, :).';
    s3(:, :, jj) = exp(-1i * (Rn * Kw));
end

for jj = 1:Nr
    Temp(:, :) = s3(:, jj, :);
    Temp(:, :) = fty(Temp);
    s3(:, jj, :) = Temp(:, :);
end

for jj = 1:Nr
    Temp(:, :) = s3(:, jj, :);
    Temp(:, :) = ftx(Temp);
    s3(:, jj, :) = Temp(:, :);
end

rho_ref = [0.0, 0.15, 0.30];
Three_Image = zeros(Na, length(rho_ref), Nh);
for nhh = 1:Nh
    for jj = 1:length(rho_ref)
        rn_ref = sqrt(R^2 + rho_ref(jj)^2 - 2 * R * rho_ref(jj) * cos(u));
        FT_rn_ref = ftx(exp(1i * rn_ref.' * Kwz(nhh, :)) .* (ones(Na, 1) * Kw / 2));
        Temp = s3(:, :, nhh);
        Temp = Temp .* FT_rn_ref;
        Three_Image(:, jj, nhh) = iftx(sum(Temp.').');
    end
end

for jj = 1:length(rho_ref)
    Temp = reshape(Three_Image(:, jj, :), [Na, Nh]);
    Temp = ifty(Temp);
    Three_Image(:, jj, :) = Temp(:, :);
end

audit_file = fullfile(output_root, 'matlab_engine_notes.md');
fid = fopen(audit_file, 'w');
fprintf(fid, '# matlab_engine_notes\n\n');
fprintf(fid, '- MATLAB executable: R2018b\n');
fprintf(fid, '- Source root: `%s`\n', matlab_root);
fprintf(fid, '- Verified helpers: `ftx`, `fty`, `iftx`, `ifty`\n');
fprintf(fid, '- Synthetic point target: rho=0.15 m, z=0.00 m, local azimuth window=91, local height window=%d\n', Nh);
[peak_value, linear_idx] = max(abs(Three_Image(:)));
[peak_u, peak_rho, peak_h] = ind2sub(size(Three_Image), linear_idx);
fprintf(fid, '- Peak magnitude: %.6f\n', peak_value);
fprintf(fid, '- Peak indices: u=%d, rho_ref=%d, h=%d\n', peak_u, peak_rho, peak_h);
fclose(fid);

disp(['Wrote ', audit_file]);
