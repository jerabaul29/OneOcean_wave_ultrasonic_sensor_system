#ifndef EXPRESSION_MATCHER_H
#define EXPRESSION_MATCHER_H

#include "Arduino.h"
#include "math.h"

#define EXPRESSION_MATCHER_DEBUG 0

class ExpressionMatcher{
    public:
        ExpressionMatcher(char const to_match[], size_t const size_in);
        bool match(char crrt_char);

    private:
        void reset_match_index(void);

        constexpr static size_t max_to_match_size {128};
        char arr_to_match[max_to_match_size];
        size_t current_match_size;

        size_t current_match_index;
};

#endif
