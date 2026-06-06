#include <algorithm>
#include <cerrno>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

struct Node {
    virtual ~Node() = default;
    virtual double eval(double x, double y) const = 0;
};

struct NumberNode final : Node {
    explicit NumberNode(double value) : value(value) {}
    double eval(double, double) const override { return value; }
    double value;
};

struct VariableNode final : Node {
    explicit VariableNode(char axis) : axis(axis) {}
    double eval(double x, double y) const override { return axis == 'y' ? y : x; }
    char axis;
};

struct UnaryNode final : Node {
    UnaryNode(char op, std::unique_ptr<Node> child)
        : op(op), child(std::move(child)) {}

    double eval(double x, double y) const override {
        const double value = child->eval(x, y);
        return op == '-' ? -value : value;
    }

    char op;
    std::unique_ptr<Node> child;
};

struct BinaryNode final : Node {
    BinaryNode(char op, std::unique_ptr<Node> left, std::unique_ptr<Node> right)
        : op(op), left(std::move(left)), right(std::move(right)) {}

    double eval(double x, double y) const override {
        const double a = left->eval(x, y);
        const double b = right->eval(x, y);
        switch (op) {
            case '+': return a + b;
            case '-': return a - b;
            case '*': return a * b;
            case '/': return a / b;
            case '^': return std::pow(a, b);
            default: return std::numeric_limits<double>::quiet_NaN();
        }
    }

    char op;
    std::unique_ptr<Node> left;
    std::unique_ptr<Node> right;
};

enum class FunctionKind {
    Sin,
    Cos,
    Tan,
    Asin,
    Acos,
    Atan,
    Sinh,
    Cosh,
    Tanh,
    Exp,
    Log,
    Sqrt,
    Abs,
    Floor,
    Ceil,
    Pow,
    Min,
    Max
};

struct FunctionNode final : Node {
    FunctionNode(FunctionKind kind, std::unique_ptr<Node> first, std::unique_ptr<Node> second = nullptr)
        : kind(kind), first(std::move(first)), second(std::move(second)) {}

    double eval(double x, double y) const override {
        const double a = first->eval(x, y);
        switch (kind) {
            case FunctionKind::Sin: return std::sin(a);
            case FunctionKind::Cos: return std::cos(a);
            case FunctionKind::Tan: return std::tan(a);
            case FunctionKind::Asin: return std::asin(a);
            case FunctionKind::Acos: return std::acos(a);
            case FunctionKind::Atan: return std::atan(a);
            case FunctionKind::Sinh: return std::sinh(a);
            case FunctionKind::Cosh: return std::cosh(a);
            case FunctionKind::Tanh: return std::tanh(a);
            case FunctionKind::Exp: return std::exp(a);
            case FunctionKind::Log: return std::log(a);
            case FunctionKind::Sqrt: return std::sqrt(a);
            case FunctionKind::Abs: return std::fabs(a);
            case FunctionKind::Floor: return std::floor(a);
            case FunctionKind::Ceil: return std::ceil(a);
            case FunctionKind::Pow: return std::pow(a, second->eval(x, y));
            case FunctionKind::Min: return std::min(a, second->eval(x, y));
            case FunctionKind::Max: return std::max(a, second->eval(x, y));
        }
        return std::numeric_limits<double>::quiet_NaN();
    }

    FunctionKind kind;
    std::unique_ptr<Node> first;
    std::unique_ptr<Node> second;
};

std::string lower_copy(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return value;
}

class Parser {
public:
    explicit Parser(std::string input) : input_(std::move(input)) {}

    std::unique_ptr<Node> parse() {
        auto node = parse_expression();
        skip_spaces();
        if (pos_ != input_.size()) {
            throw std::runtime_error("Unexpected token near position " + std::to_string(pos_));
        }
        return node;
    }

private:
    std::unique_ptr<Node> parse_expression() {
        auto node = parse_term();
        while (true) {
            skip_spaces();
            if (match('+')) {
                node = std::make_unique<BinaryNode>('+', std::move(node), parse_term());
            } else if (match('-')) {
                node = std::make_unique<BinaryNode>('-', std::move(node), parse_term());
            } else {
                return node;
            }
        }
    }

    std::unique_ptr<Node> parse_term() {
        auto node = parse_unary();
        while (true) {
            skip_spaces();
            if (match('*')) {
                node = std::make_unique<BinaryNode>('*', std::move(node), parse_unary());
            } else if (match('/')) {
                node = std::make_unique<BinaryNode>('/', std::move(node), parse_unary());
            } else {
                return node;
            }
        }
    }

    std::unique_ptr<Node> parse_power() {
        auto node = parse_primary();
        skip_spaces();
        if (match('^')) {
            node = std::make_unique<BinaryNode>('^', std::move(node), parse_unary());
        }
        return node;
    }

    std::unique_ptr<Node> parse_unary() {
        skip_spaces();
        if (match('+')) {
            return std::make_unique<UnaryNode>('+', parse_unary());
        }
        if (match('-')) {
            return std::make_unique<UnaryNode>('-', parse_unary());
        }
        return parse_power();
    }

    std::unique_ptr<Node> parse_primary() {
        skip_spaces();
        if (match('(')) {
            auto node = parse_expression();
            expect(')');
            return node;
        }
        if (std::isdigit(peek()) || peek() == '.') {
            return parse_number();
        }
        if (std::isalpha(peek()) || peek() == '_') {
            return parse_identifier();
        }
        throw std::runtime_error("Expected expression near position " + std::to_string(pos_));
    }

    std::unique_ptr<Node> parse_number() {
        const char* start = input_.c_str() + pos_;
        char* end = nullptr;
        errno = 0;
        const double value = std::strtod(start, &end);
        if (end == start || errno == ERANGE) {
            throw std::runtime_error("Invalid number near position " + std::to_string(pos_));
        }
        pos_ = static_cast<std::size_t>(end - input_.c_str());
        return std::make_unique<NumberNode>(value);
    }

    std::unique_ptr<Node> parse_identifier() {
        const std::size_t start = pos_;
        while (std::isalnum(peek()) || peek() == '_') {
            ++pos_;
        }
        const std::string raw = input_.substr(start, pos_ - start);
        const std::string id = lower_copy(raw);

        if (id == "x" || id == "y") {
            return std::make_unique<VariableNode>(id[0]);
        }
        if (id == "pi") {
            return std::make_unique<NumberNode>(std::acos(-1.0));
        }
        if (id == "e") {
            return std::make_unique<NumberNode>(std::exp(1.0));
        }

        skip_spaces();
        expect('(');
        auto first = parse_expression();
        std::unique_ptr<Node> second;
        skip_spaces();
        if (match(',')) {
            second = parse_expression();
        }
        expect(')');

        const auto kind = function_kind(id, second != nullptr);
        if (requires_two_arguments(kind) && !second) {
            throw std::runtime_error(raw + " requires two arguments");
        }
        if (!requires_two_arguments(kind) && second) {
            throw std::runtime_error(raw + " takes one argument");
        }
        return std::make_unique<FunctionNode>(kind, std::move(first), std::move(second));
    }

    static bool requires_two_arguments(FunctionKind kind) {
        return kind == FunctionKind::Pow || kind == FunctionKind::Min || kind == FunctionKind::Max;
    }

    static FunctionKind function_kind(const std::string& id, bool has_second) {
        if (id == "sin") return FunctionKind::Sin;
        if (id == "cos") return FunctionKind::Cos;
        if (id == "tan") return FunctionKind::Tan;
        if (id == "asin" || id == "arcsin") return FunctionKind::Asin;
        if (id == "acos" || id == "arccos") return FunctionKind::Acos;
        if (id == "atan" || id == "arctan") return FunctionKind::Atan;
        if (id == "sinh") return FunctionKind::Sinh;
        if (id == "cosh") return FunctionKind::Cosh;
        if (id == "tanh") return FunctionKind::Tanh;
        if (id == "exp") return FunctionKind::Exp;
        if (id == "log" || id == "ln") return FunctionKind::Log;
        if (id == "sqrt") return FunctionKind::Sqrt;
        if (id == "abs") return FunctionKind::Abs;
        if (id == "floor") return FunctionKind::Floor;
        if (id == "ceil") return FunctionKind::Ceil;
        if (id == "pow") return FunctionKind::Pow;
        if (id == "min") return FunctionKind::Min;
        if (id == "max") return FunctionKind::Max;

        std::string suffix = has_second ? " with two arguments" : "";
        throw std::runtime_error("Unknown function: " + id + suffix);
    }

    void skip_spaces() {
        while (std::isspace(peek())) {
            ++pos_;
        }
    }

    char peek() const {
        if (pos_ >= input_.size()) {
            return '\0';
        }
        return input_[pos_];
    }

    bool match(char expected) {
        if (peek() == expected) {
            ++pos_;
            return true;
        }
        return false;
    }

    void expect(char expected) {
        skip_spaces();
        if (!match(expected)) {
            throw std::runtime_error(std::string("Expected '") + expected + "' near position " + std::to_string(pos_));
        }
    }

    std::string input_;
    std::size_t pos_ = 0;
};

struct EvalState {
    explicit EvalState(const Node& root) : root(root) {}

    double operator()(double x) {
        return eval(x, 0.0);
    }

    double eval(double x, double y) {
        ++evaluations;
        const double value = root.eval(x, y);
        if (!std::isfinite(value)) {
            throw std::runtime_error("Function evaluated to a non-finite value");
        }
        return value;
    }

    const Node& root;
    long long evaluations = 0;
};

struct IntegralResult {
    double value = 0.0;
    double error = 0.0;
};

double simpson(double a, double b, double fa, double fm, double fb) {
    return (b - a) * (fa + 4.0 * fm + fb) / 6.0;
}

IntegralResult adaptive_simpson(
    EvalState& f,
    double a,
    double b,
    double eps,
    double whole,
    double fa,
    double fm,
    double fb,
    int depth
) {
    const double mid = (a + b) * 0.5;
    const double left_mid = (a + mid) * 0.5;
    const double right_mid = (mid + b) * 0.5;
    const double flm = f(left_mid);
    const double frm = f(right_mid);
    const double left = simpson(a, mid, fa, flm, fm);
    const double right = simpson(mid, b, fm, frm, fb);
    const double delta = left + right - whole;
    const double tolerance = 15.0 * eps;

    if (depth <= 0 || std::fabs(delta) <= tolerance) {
        return {left + right + delta / 15.0, std::fabs(delta) / 15.0};
    }

    const IntegralResult l = adaptive_simpson(f, a, mid, eps * 0.5, left, fa, flm, fm, depth - 1);
    const IntegralResult r = adaptive_simpson(f, mid, b, eps * 0.5, right, fm, frm, fb, depth - 1);
    return {l.value + r.value, l.error + r.error};
}

IntegralResult integrate(EvalState& f, double lower, double upper, double eps) {
    if (!std::isfinite(lower) || !std::isfinite(upper)) {
        throw std::runtime_error("C++ engine currently expects finite bounds");
    }
    if (lower == upper) {
        return {0.0, 0.0};
    }

    double sign = 1.0;
    double a = lower;
    double b = upper;
    if (b < a) {
        std::swap(a, b);
        sign = -1.0;
    }

    const int panels = 32;
    const int max_depth = 24;
    const double width = (b - a) / static_cast<double>(panels);
    IntegralResult total;

    for (int i = 0; i < panels; ++i) {
        const double left = a + width * static_cast<double>(i);
        const double right = (i == panels - 1) ? b : left + width;
        const double mid = (left + right) * 0.5;
        const double fa = f(left);
        const double fm = f(mid);
        const double fb = f(right);
        const double whole = simpson(left, right, fa, fm, fb);
        const IntegralResult part = adaptive_simpson(
            f,
            left,
            right,
            eps / static_cast<double>(panels),
            whole,
            fa,
            fm,
            fb,
            max_depth
        );
        total.value += part.value;
        total.error += part.error;
    }

    total.value *= sign;
    return total;
}

double simpson_weight(int index, int panels) {
    if (index == 0 || index == panels) {
        return 1.0;
    }
    return index % 2 == 0 ? 2.0 : 4.0;
}

double composite_simpson_2d(
    EvalState& f,
    double x_lower,
    double x_upper,
    double y_lower,
    double y_upper,
    int panels
) {
    if (!std::isfinite(x_lower) || !std::isfinite(x_upper) ||
        !std::isfinite(y_lower) || !std::isfinite(y_upper)) {
        throw std::runtime_error("C++ double engine currently expects finite rectangular bounds");
    }
    if (x_lower == x_upper || y_lower == y_upper) {
        return 0.0;
    }

    double sign = 1.0;
    double xa = x_lower;
    double xb = x_upper;
    double ya = y_lower;
    double yb = y_upper;
    if (xb < xa) {
        std::swap(xa, xb);
        sign *= -1.0;
    }
    if (yb < ya) {
        std::swap(ya, yb);
        sign *= -1.0;
    }

    if (panels % 2 != 0) {
        ++panels;
    }

    const double hx = (xb - xa) / static_cast<double>(panels);
    const double hy = (yb - ya) / static_cast<double>(panels);
    double sum = 0.0;

    for (int i = 0; i <= panels; ++i) {
        const double xv = xa + hx * static_cast<double>(i);
        const double wx = simpson_weight(i, panels);
        for (int j = 0; j <= panels; ++j) {
            const double yv = ya + hy * static_cast<double>(j);
            const double wy = simpson_weight(j, panels);
            sum += wx * wy * f.eval(xv, yv);
        }
    }

    return sign * sum * hx * hy / 9.0;
}

IntegralResult integrate_double(
    EvalState& f,
    double x_lower,
    double x_upper,
    double y_lower,
    double y_upper
) {
    const double coarse = composite_simpson_2d(f, x_lower, x_upper, y_lower, y_upper, 32);
    const double fine = composite_simpson_2d(f, x_lower, x_upper, y_lower, y_upper, 64);
    return {fine, std::fabs(fine - coarse) / 15.0};
}

std::string json_escape(const std::string& input) {
    std::ostringstream out;
    for (const char ch : input) {
        switch (ch) {
            case '\\': out << "\\\\"; break;
            case '"': out << "\\\""; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default: out << ch; break;
        }
    }
    return out.str();
}

double parse_double_arg(const char* value, const std::string& name) {
    char* end = nullptr;
    errno = 0;
    const double parsed = std::strtod(value, &end);
    if (end == value || *end != '\0' || errno == ERANGE) {
        throw std::runtime_error("Invalid " + name + ": " + value);
    }
    return parsed;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc >= 2 && std::string(argv[1]) == "--double") {
        if (argc < 7 || argc > 8) {
            std::cout << "{\"ok\":false,\"error\":\"Usage: integrator --double <expression> <x_lower> <x_upper> <y_lower> <y_upper> [eps]\"}\n";
            return 2;
        }

        try {
            const std::string expression = argv[2];
            const double x_lower = parse_double_arg(argv[3], "x lower bound");
            const double x_upper = parse_double_arg(argv[4], "x upper bound");
            const double y_lower = parse_double_arg(argv[5], "y lower bound");
            const double y_upper = parse_double_arg(argv[6], "y upper bound");

            Parser parser(expression);
            const std::unique_ptr<Node> root = parser.parse();
            EvalState f(*root);
            const IntegralResult result = integrate_double(f, x_lower, x_upper, y_lower, y_upper);

            std::cout << std::setprecision(17)
                      << "{\"ok\":true,"
                      << "\"value\":" << result.value << ','
                      << "\"estimated_error\":" << result.error << ','
                      << "\"evaluations\":" << f.evaluations << ','
                      << "\"method\":\"composite_simpson_2d_cpp\","
                      << "\"engine\":\"cpp\""
                      << "}\n";
            return 0;
        } catch (const std::exception& ex) {
            std::cout << "{\"ok\":false,\"error\":\"" << json_escape(ex.what()) << "\"}\n";
            return 1;
        }
    }

    if (argc < 4 || argc > 5) {
        std::cout << "{\"ok\":false,\"error\":\"Usage: integrator <expression> <lower> <upper> [eps]\"}\n";
        return 2;
    }

    try {
        const std::string expression = argv[1];
        const double lower = parse_double_arg(argv[2], "lower bound");
        const double upper = parse_double_arg(argv[3], "upper bound");
        const double eps = argc == 5 ? parse_double_arg(argv[4], "epsilon") : 1e-8;

        Parser parser(expression);
        const std::unique_ptr<Node> root = parser.parse();
        EvalState f(*root);
        const IntegralResult result = integrate(f, lower, upper, std::max(eps, 1e-14));

        std::cout << std::setprecision(17)
                  << "{\"ok\":true,"
                  << "\"value\":" << result.value << ','
                  << "\"estimated_error\":" << result.error << ','
                  << "\"evaluations\":" << f.evaluations << ','
                  << "\"method\":\"adaptive_simpson_cpp\","
                  << "\"engine\":\"cpp\""
                  << "}\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cout << "{\"ok\":false,\"error\":\"" << json_escape(ex.what()) << "\"}\n";
        return 1;
    }
}
