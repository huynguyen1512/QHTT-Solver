import streamlit as st
import pandas as pd
from fractions import Fraction

# ==========================================
# CÁC HÀM HỖ TRỢ LATEX VÀ TOÁN HỌC
# ==========================================
def to_latex_frac(val: Fraction):
    """Chuyển đổi Fraction thành chuỗi phân số LaTeX"""
    if val.denominator == 1:
        return str(val.numerator)
    if val.numerator < 0:
        return f"-\\frac{{{-val.numerator}}}{{{val.denominator}}}"
    return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"

def format_term(coef: Fraction, var_name: str, is_first: bool = False):
    """Định dạng một số hạng trong phương trình đại số"""
    if coef == 0:
        return ""
    
    sign_str = ""
    if is_first:
        if coef < 0: sign_str = "-"
    else:
        sign_str = " + " if coef > 0 else " - "
        
    abs_coef = abs(coef)
    coef_str = "" if abs_coef == 1 else to_latex_frac(abs_coef)
    
    return f"{sign_str}{coef_str}{var_name}"

# ==========================================
# LÕI THUẬT TOÁN ĐƠN HÌNH TỪ VỰNG
# ==========================================
class SimplexDictionary:
    def __init__(self, c_dict, A_dict, b_dict, original_v, method_choice):
        self.N = list(c_dict.keys())
        self.B = list(b_dict.keys())
        self.c = c_dict.copy()
        self.A = {i: A_dict[i].copy() for i in self.B}
        self.b = b_dict.copy()
        self.v = original_v
        
        self.method = method_choice
        self.steps_log = []
        
    def log_dictionary(self, title, entering=None, leaving=None):
        """Xuất từ vựng hiện tại ra định dạng LaTeX có đánh dấu mũi tên"""
        latex_str = f"**{title}**\n\n"
        
        # Phương trình của các biến cơ sở
        for i in self.B:
            var_i_str = f"\\leftarrow {i}" if i == leaving else i
            
            # Xây dựng vế phải
            rhs = ""
            first_term = True
            
            if self.b[i] != 0 or all(self.A[i][j] == 0 for j in self.N):
                rhs += to_latex_frac(self.b[i])
                first_term = False
                
            for j in self.N:
                coef = -self.A[i][j]
                if coef != 0:
                    var_j_str = f"\\overset{{\\downarrow}}{{{j}}}" if j == entering else j
                    rhs += format_term(coef, var_j_str, is_first=first_term)
                    first_term = False
                    
            if rhs == "": rhs = "0"
            latex_str += f"$$ {var_i_str} = {rhs} $$\n"
            
        # Phương trình hàm mục tiêu
        obj_rhs = ""
        first_term = True
        if self.v != 0 or all(self.c[j] == 0 for j in self.N):
            obj_rhs += to_latex_frac(self.v)
            first_term = False
            
        for j in self.N:
            coef = self.c[j]
            if coef != 0:
                var_j_str = f"\\overset{{\\downarrow}}{{{j}}}" if j == entering else j
                obj_rhs += format_term(coef, var_j_str, is_first=first_term)
                first_term = False
                
        if obj_rhs == "": obj_rhs = "0"
        latex_str += f"$$ w = {obj_rhs} $$\n"
        
        self.steps_log.append(latex_str)

    def pivot(self, entering, leaving):
        """Thực hiện một phép xoay (Pivot)"""
        A_rk = self.A[leaving][entering]
        new_b_leaving = self.b[leaving] / A_rk
        new_A_leaving = {}
        
        for j in self.N:
            if j == entering:
                new_A_leaving[leaving] = Fraction(1) / A_rk
            else:
                new_A_leaving[j] = self.A[leaving][j] / A_rk

        for i in self.B:
            if i == leaving: continue
            A_ik = self.A[i][entering]
            self.b[i] -= A_ik * new_b_leaving
            for j in self.N:
                if j == entering:
                    self.A[i][leaving] = -A_ik * new_A_leaving[leaving]
                else:
                    self.A[i][j] -= A_ik * new_A_leaving[j]
            del self.A[i][entering]

        c_k = self.c[entering]
        self.v += c_k * new_b_leaving
        for j in self.N:
            if j == entering:
                self.c[leaving] = -c_k * new_A_leaving[leaving]
            else:
                self.c[j] -= c_k * new_A_leaving[j]
        del self.c[entering]

        self.b[entering] = new_b_leaving
        self.A[entering] = new_A_leaving
        del self.b[leaving]
        del self.A[leaving]

        self.N.remove(entering)
        self.N.append(leaving)
        self.B.remove(leaving)
        self.B.append(entering)

        # Sắp xếp lại chỉ số biến để hiển thị đẹp hơn
        self.N.sort(key=lambda x: (x.split('_')[0], x))
        self.B.sort(key=lambda x: (x.split('_')[0], x))

    def solve(self):
        if self.method == "Two-Phase":
            orig_c = self.c.copy()
            orig_v = self.v
            
            # Khởi tạo Pha 1
            self.N.append("x_0")
            for i in self.B:
                self.A[i]["x_0"] = Fraction(-1)
            
            self.c = {j: Fraction(0) for j in self.N}
            self.c["x_0"] = Fraction(1)
            self.v = Fraction(0)
            
            # Xoay ép buộc
            leaving = min(self.b, key=self.b.get)
            entering = "x_0"
            self.log_dictionary("Từ vựng xuất phát (Chưa khả thi):", entering, leaving)
            self.pivot(entering, leaving)
            
            # Giải Pha 1 bằng Dantzig
            status = self._run_phase(rule="Dantzig", phase_name="Pha 1")
            if status != "Optimal": return status
            if self.v > 0: return "Infeasible"
            
            # Loại bỏ x_0 và khôi phục Pha 2
            if "x_0" in self.B: return "Degenerate x_0"
            self.N.remove("x_0")
            for i in self.B: del self.A[i]["x_0"]
            
            self.v = orig_v
            self.c = {j: Fraction(0) for j in self.N}
            for j in orig_c:
                if j in self.N:
                    self.c[j] += orig_c[j]
                elif j in self.B:
                    self.v += orig_c[j] * self.b[j]
                    for k in self.N:
                        self.c[k] -= orig_c[j] * self.A[j][k]
                        
            self.log_dictionary("Từ vựng bắt đầu Pha 2 (Đã khôi phục hàm mục tiêu):")
            return self._run_phase(rule="Dantzig", phase_name="Pha 2")
            
        else:
            # Giải trực tiếp bằng Dantzig hoặc Bland
            return self._run_phase(rule=self.method, phase_name="Bài toán")

    def _run_phase(self, rule, phase_name):
        iteration = 1
        while True:
            if all(val >= 0 for val in self.c.values()):
                self.log_dictionary(f"Từ vựng Tối ưu ({phase_name}):")
                return "Optimal"
                
            entering = None
            if rule == "Bland":
                candidates = [j for j in self.N if self.c[j] < 0]
                entering = min(candidates, key=lambda x: x) # So sánh chuỗi/chỉ số
            else:
                entering = min(self.N, key=lambda j: self.c[j])

            leaving_candidates = []
            for i in self.B:
                if self.A[i][entering] > 0:
                    ratio = self.b[i] / self.A[i][entering]
                    leaving_candidates.append((ratio, i))
                    
            if not leaving_candidates:
                return "Unbounded"
                
            min_ratio = min(leaving_candidates, key=lambda x: x[0])[0]
            tied_leaving = [i for r, i in leaving_candidates if r == min_ratio]
            
            if rule == "Bland":
                leaving = min(tied_leaving, key=lambda x: x)
            else:
                leaving = tied_leaving[0]

            self.log_dictionary(f"Lần xoay {iteration}:", entering, leaving)
            self.pivot(entering, leaving)
            iteration += 1

# ==========================================
# GIAO DIỆN & TIỀN XỬ LÝ (ĐÃ CẬP NHẬT UI)
# ==========================================
def get_subscript(n):
    """Hàm hỗ trợ chuyển số thành chỉ số dưới (subscript) dạng Unicode"""
    return str(n).translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))

st.set_page_config(page_title="General LP Solver", layout="wide")
st.title("🧮 Trình giải Quy Hoạch Tuyến Tính Tổng Quát")
st.markdown("---")

# Cài đặt kích thước
st.sidebar.header("⚙️ Kích thước bài toán")
num_vars = st.sidebar.number_input("Số lượng biến (n):", 1, 10, 2)
num_constraints = st.sidebar.number_input("Số lượng ràng buộc (m):", 1, 10, 3)

# ---------------------------------------------------------
st.subheader("1. Hàm mục tiêu (Objective Function)")
st.info("Nhập các hệ số $c_j$ để định hình hàm mục tiêu: $Z = c_1 x_1 + c_2 x_2 + \dots + c_n x_n$")

obj_type = st.radio("Mục tiêu của bài toán:", ["Max", "Min"], horizontal=True)

cols = st.columns(num_vars)
C_orig = []
for j in range(num_vars):
    with cols[j]:
        var_name = f"x{get_subscript(j+1)}"
        val = st.number_input(f"Hệ số của {var_name}", value=0.0, step=1.0, key=f"C_{j}")
        C_orig.append(Fraction(val))

# ---------------------------------------------------------
st.subheader("2. Dấu của biến (Variable Conditions)")
st.info("Xác định miền giá trị cho từng biến (không âm, không dương, hoặc tùy ý).")

cols = st.columns(num_vars)
var_signs = []
for j in range(num_vars):
    with cols[j]:
        var_name = f"x{get_subscript(j+1)}"
        # Đã đổi thành ký hiệu toán học chuẩn Unicode
        sign = st.selectbox(var_name, ["≥ 0", "≤ 0", "Tùy ý"], key=f"vsign_{j}")
        var_signs.append(sign)

# ---------------------------------------------------------
st.subheader("3. Các hệ ràng buộc (Constraints)")
st.info("Nhập ma trận hệ số $A$, chọn dấu (≤, ≥, =), và nhập vế phải $b$.")

A_orig = []
B_orig = []
cons_signs = []

# --- Tạo thanh tiêu đề cột (Header) cho đẹp ---
header_cols = st.columns(num_vars + 2)
for j in range(num_vars):
    header_cols[j].markdown(f"<div style='text-align: center; font-weight: bold;'>x{get_subscript(j+1)}</div>", unsafe_allow_html=True)
header_cols[num_vars].markdown("<div style='text-align: center; font-weight: bold;'>Dấu</div>", unsafe_allow_html=True)
header_cols[num_vars+1].markdown("<div style='text-align: center; font-weight: bold;'>b</div>", unsafe_allow_html=True)
# ----------------------------------------------

for i in range(num_constraints):
    cols = st.columns(num_vars + 2)
    row = []
    for j in range(num_vars):
        with cols[j]:
            val = st.number_input(f"A_{i}_{j}", value=0.0, step=1.0, key=f"A_{i}_{j}", label_visibility="collapsed")
            row.append(Fraction(val))
    A_orig.append(row)
    
    with cols[num_vars]:
        # Đã đổi thành ký hiệu toán học chuẩn Unicode
        sign = st.selectbox("Dấu", ["≤", "≥", "="], key=f"csign_{i}", label_visibility="collapsed")
        cons_signs.append(sign)
        
    with cols[num_vars+1]:
        val = st.number_input("b", value=0.0, step=1.0, key=f"B_{i}", label_visibility="collapsed")
        B_orig.append(Fraction(val))

st.markdown("---")
show_steps = st.checkbox("Hiển thị chi tiết quá trình xoay từ vựng", value=True)

if st.button("🚀 Giải Bài Toán", type="primary", use_container_width=True):
    # --- BƯỚC 1: CHUẨN HÓA BÀI TOÁN TỔNG QUÁT ---
    std_c_list = []
    std_vars_map = [] 
    
    # Chuẩn hóa biến (Cập nhật logic dò chuỗi Unicode)
    for j in range(num_vars):
        c_val = C_orig[j] if obj_type == "Min" else -C_orig[j]
        if var_signs[j] == "≥ 0":
            std_c_list.append(c_val)
            std_vars_map.append(f"x_{j+1}")
        elif var_signs[j] == "≤ 0":
            std_c_list.append(-c_val)
            std_vars_map.append(f"x'_{j+1}")
        elif var_signs[j] == "Tùy ý":
            std_c_list.extend([c_val, -c_val])
            std_vars_map.extend([f"x_{j+1}^+", f"x_{j+1}^-"])
            
    # Chuẩn hóa ràng buộc (Cập nhật logic dò chuỗi Unicode)
    std_A_matrix = []
    std_b_list = []
    
    for i in range(num_constraints):
        row = []
        for j in range(num_vars):
            a_val = A_orig[i][j]
            if var_signs[j] == "≥ 0": row.append(a_val)
            elif var_signs[j] == "≤ 0": row.append(-a_val)
            elif var_signs[j] == "Tùy ý": row.extend([a_val, -a_val])
            
        if cons_signs[i] == "≤":
            std_A_matrix.append(row)
            std_b_list.append(B_orig[i])
        elif cons_signs[i] == "≥":
            std_A_matrix.append([-x for x in row])
            std_b_list.append(-B_orig[i])
        elif cons_signs[i] == "=":
            std_A_matrix.append(row)
            std_b_list.append(B_orig[i])
            std_A_matrix.append([-x for x in row])
            std_b_list.append(-B_orig[i])

    # Khởi tạo Dictionary
    c_dict = {std_vars_map[j]: std_c_list[j] for j in range(len(std_vars_map))}
    b_dict = {}
    A_dict = {}
    
    slack_idx = 1
    for i in range(len(std_b_list)):
        slack_var = f"x_{{{num_vars + slack_idx}}}"
        b_dict[slack_var] = std_b_list[i]
        A_dict[slack_var] = {std_vars_map[j]: std_A_matrix[i][j] for j in range(len(std_vars_map))}
        slack_idx += 1

    # --- BƯỚC 2: AUTO-ROUTING (TỰ ĐỘNG CHỌN PHƯƠNG PHÁP) ---
    min_b = min(b_dict.values())
    if min_b < 0:
        chosen_method = "Two-Phase"
        msg = "Hệ số $b_i$ của từ vựng xuất phát có chứa giá trị âm. Chương trình tự động áp dụng: **Phương pháp Đơn hình 2 Pha**."
    elif any(v == 0 for v in b_dict.values()):
        chosen_method = "Bland"
        msg = "Từ vựng xuất phát khả thi nhưng rơi vào trạng thái suy biến ($b_i = 0$). Chương trình tự động áp dụng: **Quy tắc Bland**."
    else:
        chosen_method = "Dantzig"
        msg = "Từ vựng xuất phát khả thi nghiêm ngặt ($b_i > 0$). Chương trình tự động áp dụng: **Quy tắc Dantzig**."

    st.success(msg)

    # --- BƯỚC 3: GIẢI VÀ HIỂN THỊ ---
    solver = SimplexDictionary(c_dict, A_dict, b_dict, Fraction(0), chosen_method)
    
    if chosen_method != "Two-Phase":
        solver.log_dictionary("Từ vựng xuất phát:")
        
    status = solver.solve()
    
    st.divider()
    if status == "Optimal":
        st.markdown("### ✅ Đã tìm thấy nghiệm tối ưu!")
        final_obj = -solver.v if obj_type == "Max" else solver.v
        st.markdown(f"**Giá trị hàm mục tiêu tối ưu:** $Z = {to_latex_frac(final_obj)}$")
    elif status == "Infeasible":
        st.error("❌ Bài toán vô nghiệm .")
    elif status == "Unbounded":
        st.warning("⚠️ Bài toán không giới nội (Vô cực).")
        
    if show_steps:
        st.subheader("📜 Quá trình xoay Từ Vựng")
        for step in solver.steps_log:
            st.markdown(step)
